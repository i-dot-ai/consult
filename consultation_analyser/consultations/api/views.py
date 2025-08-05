from collections import defaultdict

import orjson
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from magic_link.exceptions import InvalidLink
from magic_link.models import MagicLink
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .. import models
from ..views.sessions import send_magic_link_if_email_exists
from .filters import QuestionFilter
from .permissions import CanSeeConsultation, HasDashboardAccess
from .serializers import (
    ConsultationSerializer,
    DemographicAggregationsSerializer,
    DemographicOptionsSerializer,
    FilterSerializer,
    MultiChoiceAnswerCount,
    QuestionSerializer,
    ThemeAggregationsSerializer,
    ThemeInformationSerializer,
    UserSerializer,
)
from .utils import (
    build_respondent_data_fast,
    build_response_filter_query,
    get_filtered_responses_with_themes,
    parse_filters_from_serializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Returns the current logged-in user's information
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class ConsultationViewSet(ReadOnlyModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [HasDashboardAccess]
    filterset_fields = ["slug"]

    def get_queryset(self):
        return models.Consultation.objects.filter(users=self.request.user).order_by("-created_at")


class QuestionViewSet(ReadOnlyModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    filterset_class = QuestionFilter

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return models.Question.objects.filter(
            consultation__id=consultation_uuid, consultation__users=self.request.user
        ).order_by("-created_at")

    @action(
        detail=True,
        methods=["get"],
        url_path="multi-choice-response-count",
        serializer_class=MultiChoiceAnswerCount,
    )
    def multi_choice_response_count(self, request, pk=None, consultation_pk=None):
        question = self.get_object()
        answer_count = question.response_set.values("chosen_options__text").annotate(
            response_count=Count("id")
        )
        serializer = self.get_serializer(instance=answer_count, many=True)
        return JsonResponse(data=serializer.data, safe=False)

    @action(detail=True, methods=["get"], url_path="demographic-options")
    def demographic_options(self, request, pk=None, consultation_pk=None):
        """Get all demographic options for a consultation"""
        question = self.get_object()
        consultation = question.consultation

        # Get all demographic fields and their possible values from normalized storage
        options = (
            models.DemographicOption.objects.filter(consultation=consultation)
            .values_list("field_name", "field_value")
            .order_by("field_name", "field_value")
        )

        result = defaultdict(list)
        for field_name, field_value in options:
            result[field_name].append(field_value)

        serializer = DemographicOptionsSerializer(data={"demographic_options": dict(result)})
        serializer.is_valid()

        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="demographic-aggregations")
    def demographic_aggregations(self, request, pk=None, consultation_pk=None):
        """Get demographic aggregations for filtered responses"""
        # Get the question object with consultation in one query
        question = self.get_object()

        # Validate query parameters
        filter_serializer = FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        # Parse filters
        filters = parse_filters_from_serializer(filter_serializer.validated_data)

        # Single query that joins responses -> respondents and gets demographics directly
        response_filter = build_response_filter_query(filters, question)
        respondents_data = models.Respondent.objects.filter(
            response__in=models.Response.objects.filter(response_filter)
        ).values_list("demographics", flat=True)

        # Aggregate in memory (much faster than nested loops)
        aggregations = defaultdict(lambda: defaultdict(int))  # type:ignore
        for demographics in respondents_data:
            if demographics:
                for field_name, field_value in demographics.items():
                    value_str = str(field_value)
                    aggregations[field_name][value_str] += 1

        result = {field: dict(counts) for field, counts in aggregations.items()}

        serializer = DemographicAggregationsSerializer(data={"demographic_aggregations": result})
        serializer.is_valid()

        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="theme-information")
    def theme_information(self, request, pk=None, consultation_pk=None):
        """Get all theme information for a question"""
        # Get the question object with consultation in one query
        question = self.get_object()

        # Get all themes for this question
        themes = models.Theme.objects.filter(question=question).values("id", "name", "description")

        serializer = ThemeInformationSerializer(data={"themes": list(themes)})
        serializer.is_valid()

        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="theme-aggregations")
    def theme_aggregations(self, request, pk=None, consultation_pk=None):
        """Get theme aggregations for filtered responses"""

        # Get the question object with consultation in one query
        question = self.get_object()

        # Validate query parameters
        filter_serializer = FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        # Parse filters
        filters = parse_filters_from_serializer(filter_serializer.validated_data)

        # Database-level aggregation using Django ORM hybrid approach
        theme_aggregations = {}

        if question.has_free_text:
            # Use the same filtering logic as FilteredResponsesAPIView
            # This ensures theme filtering uses AND logic consistently
            filtered_responses = get_filtered_responses_with_themes(question, filters)

            # Get theme counts from the filtered responses
            theme_counts = (
                models.Theme.objects.filter(responseannotation__response__in=filtered_responses)
                .values("id")
                .annotate(count=Count("responseannotation__response"))
                .order_by("id")
            )

            theme_aggregations = {str(theme["id"]): theme["count"] for theme in theme_counts}

        serializer = ThemeAggregationsSerializer(data={"theme_aggregations": theme_aggregations})
        serializer.is_valid()

        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="filtered-responses")
    def filtered_responses(self, request, pk=None, consultation_pk=None):
        """Get paginated filtered responses with orjson optimization"""
        question = self.get_object()

        # Validate query parameters
        filter_serializer = FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        # Parse filters
        filters = parse_filters_from_serializer(filter_serializer.validated_data)

        # Get pagination parameters from validated data
        page_num = filter_serializer.validated_data.get("page", 1)
        page_size = filter_serializer.validated_data.get("page_size", 50)

        # Get filtered responses with themes (optimized with prefetching)
        filtered_qs = get_filtered_responses_with_themes(question, filters)

        # Use Django's lazy pagination
        paginator = Paginator(filtered_qs, page_size, allow_empty_first_page=True)
        page_obj = paginator.page(page_num)

        # Get total respondents count for this question (single query)
        all_respondents_count = models.Response.objects.filter(question=question).count()

        # Use orjson for faster serialization of large response sets
        data = {
            "all_respondents": [build_respondent_data_fast(r) for r in page_obj.object_list],
            "has_more_pages": page_obj.has_next(),
            "respondents_total": all_respondents_count,
            "filtered_total": paginator.count,
        }

        # Return orjson-optimized HttpResponse
        return HttpResponse(orjson.dumps(data), content_type="application/json")


@api_view(["POST"])
def generate_magic_link(request):
    """
    create and email magic link
    """
    email = request.data.get("email")
    if not email:
        return Response({"detail": "Email required"}, status=400)

    send_magic_link_if_email_exists(request, email)

    return Response({"message": "Magic link sent"})


@api_view(["POST"])
def verify_magic_link(request) -> HttpResponse:
    """
    get access/refresh tokens.

    If the link is invalid, or the user is already logged in, then this
    view will raise a PermissionDenied, which will render the 403 template.

    """
    token = request.data.get("token")
    if not token:
        return Response({"detail": "token required"}, status=400)
    link = get_object_or_404(MagicLink, token=token)
    try:
        link.validate()
        link.authorize(request.user)
        refresh = RefreshToken.for_user(link.user)
    except (PermissionDenied, InvalidLink) as ex:
        link.audit(request, error=ex)
        return JsonResponse(data={"detail": str(ex.args[0])}, status=403)
    else:
        link.audit(request)
        return JsonResponse(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )
