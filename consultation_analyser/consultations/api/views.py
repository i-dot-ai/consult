from collections import defaultdict

import orjson
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from magic_link.exceptions import InvalidLink
from magic_link.models import MagicLink
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .. import models
from ..views.sessions import send_magic_link_if_email_exists
from .permissions import CanSeeConsultation, HasDashboardAccess
from .serializers import (
    ConsultationSerializer,
    CrossCuttingThemesResponseSerializer,
    DemographicAggregationsSerializer,
    DemographicOptionsSerializer,
    FilterSerializer,
    QuestionSerializer,
    ThemeAggregationsSerializer,
    ThemeInformationSerializer,
)
from .utils import (
    build_respondent_data_fast,
    build_response_filter_query,
    get_filtered_responses_with_themes,
    parse_filters_from_serializer,
)


class ConsultationViewSet(ReadOnlyModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [HasDashboardAccess]

    def get_queryset(self):
        return models.Consultation.objects.filter(users=self.request.user).order_by("-created_at")

    @action(detail=True, methods=["get"], url_path="cross-cutting-themes")
    def cross_cutting_themes(self, request, pk=None):
        """Get cross-cutting themes for a consultation with unique respondents calculation"""
        consultation = self.get_object()
        
        total_respondents = models.Respondent.objects.filter(consultation=consultation).count()
        
        cross_cutting_themes = models.CrossCuttingTheme.objects.filter(
            consultation=consultation
        ).prefetch_related('theme_assignments__theme__question')
        
        cross_cutting_themes_data = []
        
        for cct in cross_cutting_themes:
            assigned_themes = [assignment.theme for assignment in cct.theme_assignments.all()]
            theme_ids = [theme.id for theme in assigned_themes]
            
            unique_respondents_count = 0
            unique_respondents_percentage = 0.0
            
            if theme_ids:
                unique_respondents = models.Respondent.objects.filter(
                    response__annotation__themes__id__in=theme_ids,
                    consultation=consultation
                ).distinct()
                
                unique_respondents_count = unique_respondents.count()
                if total_respondents > 0:
                    unique_respondents_percentage = (unique_respondents_count / total_respondents) * 100
            
            questions_involved = set()
            themes_details = []
            for assignment in cct.theme_assignments.all():
                theme = assignment.theme
                questions_involved.add(theme.question.number)
                
                mention_count = models.Response.objects.filter(
                    annotation__themes__id=theme.id
                ).distinct().count()
                
                themes_details.append({
                    "theme_id": str(theme.id),
                    "theme_name": theme.name,
                    "theme_key": theme.key,
                    "theme_description": theme.description,
                    "question_number": theme.question.number,
                    "question_total_responses": theme.question.total_responses or 0,
                    "mention_count": mention_count
                })
            
            total_mentions = sum(theme["mention_count"] for theme in themes_details)
            
            theme_data = {
                "id": str(cct.id),
                "name": cct.name,
                "description": cct.description,
                "unique_respondents_count": unique_respondents_count,
                "unique_respondents_percentage": round(unique_respondents_percentage, 1),
                "questions": sorted(list(questions_involved)),
                "total_mentions": total_mentions,
                "themes": themes_details
            }
            
            cross_cutting_themes_data.append(theme_data)
        
        response_data = {
            "consultation_id": str(consultation.id),
            "consultation_title": consultation.title,
            "total_respondents": total_respondents,
            "cross_cutting_themes": cross_cutting_themes_data
        }
        
        serializer = CrossCuttingThemesResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)


class QuestionViewSet(ReadOnlyModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return models.Question.objects.filter(
            consultation__id=consultation_uuid, consultation__users=self.request.user
        ).order_by("-created_at")

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
        refresh = RefreshToken.for_user(request.user)
    except (PermissionDenied, InvalidLink) as ex:
        link.audit(request, error=ex)
        return JsonResponse(data={"detail": ex}, status=403)
    else:
        link.audit(request)
        return JsonResponse(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )
