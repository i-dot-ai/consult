from collections import defaultdict

from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from pgvector.django import CosineDistance
from django_filters.rest_framework import DjangoFilterBackend
from magic_link.exceptions import InvalidLink
from magic_link.models import MagicLink
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_simplejwt.tokens import AccessToken

from .. import models
from ..views.sessions import send_magic_link_if_email_exists
from ...embeddings import embed_text
from .filters import HybridSearchFilter, ResponseFilter
from .permissions import CanSeeConsultation, HasDashboardAccess
from .serializers import (
    BaseThemeSerializer,
    ConsultationSerializer,
    CrossCuttingThemeSerializer,
    DemographicAggregationsSerializer,
    DemographicOptionsSerializer,
    MultiChoiceAnswerCount,
    QuestionSerializer,
    ResponseSerializer,
    ThemeAggregationsSerializer,
    ThemeInformationSerializer,
    UserSerializer,
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
    permission_classes = [IsAuthenticated]
    filterset_fields = ["slug"]

    def get_queryset(self):
        return models.Consultation.objects.filter(users=self.request.user).order_by("-created_at")

    def get_object(self):
        consultation = get_object_or_404(models.Consultation, **self.kwargs)

        if not consultation.users.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied("You don't have permission to access this object.")

        return consultation

    # permission_classes=[CanSeeConsultation]
    @action(
        detail=True,
        methods=["get"],
        url_path="demographic-options",
    )
    def demographic_options(self, request, pk=None):
        """Get all demographic options for a consultation"""
        consultation = self.get_object()

        if not request.user.has_dashboard_access:
            raise PermissionDenied()

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


class ThemeViewSet(ReadOnlyModelViewSet):
    serializer_class = CrossCuttingThemeSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return models.CrossCuttingTheme.objects.filter(
            consultation_id=consultation_uuid, consultation__users=self.request.user
        ).order_by("-created_at")


class QuestionThemeViewSet(ModelViewSet):
    serializer_class = BaseThemeSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]

    def perform_create(self, serializer):
        question_id = self.kwargs["question_pk"]
        serializer.save(question_id=question_id)

    def get_queryset(self):
        question_uuid = self.kwargs["question_pk"]
        return models.Theme.objects.filter(question_id=question_uuid)


class QuestionViewSet(ReadOnlyModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    filterset_fields = ["has_free_text"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return (
            models.Question.objects.filter(
                consultation_id=consultation_uuid, consultation__users=self.request.user
            )
            .annotate(response_count=Count("response"))
            .order_by("-created_at")
        )

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

    @action(detail=True, methods=["post"], url_path="theme-responses")
    def theme_responses(self, request, pk=None, consultation_pk=None):
        """Get responses for a list of themes using vector similarity"""
        question = self.get_object()
        
        # Get list of theme names from request data
        themes = request.data.get('themes', [])
        
        if not themes:
            return Response({
                'status': 'error',
                'message': 'No themes provided'
            }, status=400)
        
        # Process each theme and get responses
        all_responses = {}
        
        for theme in themes:
            theme_name = theme.get('name', '').strip()
            if not theme_name:
                continue
                
            try:
                # Get embedding for the theme name
                embedded_query = embed_text(theme_name)
                distance = CosineDistance("embedding", embedded_query)
                
                # Get closest responses for this theme
                closest_responses = (
                    models.Response.objects
                    .filter(question=question)
                    .annotate(distance=distance)
                    .order_by("distance")[:10]
                    .values("free_text", "distance")
                )
                
                # Convert to list for JSON serialization
                response_list = [
                    {
                        'free_text': response['free_text'],
                        'distance': float(response['distance']) if response['distance'] else None
                    } 
                    for response in closest_responses
                ]
                
                all_responses[theme_name] = {
                    'responses': response_list,
                    'count': len(response_list)
                }
                
            except Exception as e:
                all_responses[theme_name] = {
                    'error': str(e),
                    'responses': [],
                    'count': 0
                }
        
        return Response({
            'status': 'success',
            'theme_responses': all_responses,
            'total_themes': len(themes)
        })


class BespokeResultsSetPagination(PageNumberPagination):
    # TODO: remove this, and adapt .js to mach standard PageNumberPagination
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        original = super().get_paginated_response(data).data

        question_id = self.request._request.path.split("/")[5]
        respondents_total = models.Response.objects.filter(question_id=question_id).count()

        return Response(
            {
                "respondents_total": respondents_total,
                "filtered_total": original["count"],
                "has_more_pages": bool(original["next"]),
                "all_respondents": original["results"],
            }
        )


class ResponseViewSet(ModelViewSet):
    serializer_class = ResponseSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    pagination_class = BespokeResultsSetPagination
    filter_backends = [HybridSearchFilter, DjangoFilterBackend]
    filterset_class = ResponseFilter
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        question_uuid = self.kwargs["question_pk"]
        queryset = models.Response.objects.filter(question_id=question_uuid)

        queryset = queryset.annotate(
            is_flagged=Exists(
                models.ResponseAnnotation.objects.filter(
                    response=OuterRef("pk"), flagged_by=self.request.user
                )
            )
        )
        # Apply additional FilterSet filtering (including themeFilters)
        filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return filterset.qs.distinct()

    @action(detail=False, methods=["get"], url_path="demographic-aggregations")
    def demographic_aggregations(self, request, question_pk=None, consultation_pk=None):
        """Get demographic aggregations for filtered responses"""

        aggregations = (
            models.DemographicOption.objects.filter(
                Exists(self.get_queryset().filter(respondent=OuterRef("respondent")))
            )
            .values("field_name", "field_value")
            .annotate(count=Count("respondent", distinct=True))
        )

        result = defaultdict(dict)
        for item in aggregations:
            result[item["field_name"]][item["field_value"]] = item["count"]

        result = defaultdict(dict)
        for item in aggregations:
            result[item["field_name"]][item["field_value"]] = item["count"]

        serializer = DemographicAggregationsSerializer(data={"demographic_aggregations": result})
        serializer.is_valid()

        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="theme-aggregations")
    def theme_aggregations(self, request, question_pk=None, consultation_pk=None):
        """Get theme aggregations for filtered responses"""

        # Get the question object with consultation in one query
        question = get_object_or_404(models.Question, pk=question_pk)

        # Database-level aggregation using Django ORM hybrid approach
        theme_aggregations = {}

        if question.has_free_text:
            # Get theme counts from the filtered responses
            theme_counts = (
                models.Theme.objects.filter(responseannotation__response__in=self.get_queryset())
                .values("id")
                .annotate(count=Count("responseannotation", distinct=True))
            )

            theme_aggregations = {str(theme["id"]): theme["count"] for theme in theme_counts}

        serializer = ThemeAggregationsSerializer(data={"theme_aggregations": theme_aggregations})
        serializer.is_valid()

        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="toggle-flag")
    def toggle_flag(self, request, consultation_pk=None, question_pk=None, pk=None):
        """Toggle flag on/off for the user"""
        response = self.get_object()
        if response.annotation.flagged_by.contains(request.user):
            response.annotation.flagged_by.remove(request.user)
        else:
            response.annotation.flagged_by.add(request.user)
        response.annotation.save()
        return Response()


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
        token = AccessToken.for_user(link.user)
    except (PermissionDenied, InvalidLink) as ex:
        link.audit(request, error=ex)
        return JsonResponse(data={"detail": str(ex.args[0])}, status=403)
    else:
        link.audit(request)
        # Log the user into Django session
        login(request, link.user)
        # Ensure session is created if it doesn't exist
        if not request.session.session_key:
            request.session.save()
        return JsonResponse(
            {
                "access": str(token),
                "sessionId": request.session.session_key,
            }
        )
