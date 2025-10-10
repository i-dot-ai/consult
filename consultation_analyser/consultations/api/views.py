from collections import defaultdict

from django.conf import settings
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from magic_link.exceptions import InvalidLink
from magic_link.models import MagicLink
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_simplejwt.tokens import AccessToken

from .. import models
from ..views.sessions import send_magic_link_if_email_exists
from .filters import HybridSearchFilter, ResponseFilter
from .permissions import CanSeeConsultation, HasDashboardAccess
from .serializers import (
    ConsultationSerializer,
    CrossCuttingThemeSerializer,
    DemographicAggregationsSerializer,
    DemographicOptionsSerializer,
    QuestionSerializer,
    RespondentSerializer,
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


class ConsultationViewSet(ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["slug"]
    http_method_names = ["get", "patch"]

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
        self.get_object()

        if not request.user.has_dashboard_access:
            raise PermissionDenied()

        data = (
            models.Respondent.objects.filter(consultation_id=pk)
            .order_by("demographics__field_name", "demographics__field_value")
            .values("demographics__field_name", "demographics__field_value")
            .annotate(count=Count("id"))
        )

        serializer = DemographicOptionsSerializer(instance=data, many=True)

        return Response(serializer.data)


class ThemeViewSet(ReadOnlyModelViewSet):
    serializer_class = CrossCuttingThemeSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return models.CrossCuttingTheme.objects.filter(
            consultation_id=consultation_uuid, consultation__users=self.request.user
        ).order_by("-created_at")


class RespondentViewSet(ModelViewSet):
    serializer_class = RespondentSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    filterset_fields = {"themefinder_id": ["exact", "gte", "lte"]}
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return models.Respondent.objects.filter(
            consultation_id=consultation_uuid, consultation__users=self.request.user
        ).order_by("-created_at")


class QuestionViewSet(ReadOnlyModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [CanSeeConsultation]
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

    @action(detail=True, methods=["get"], url_path="theme-information")
    def theme_information(self, request, pk=None, consultation_pk=None):
        """Get all theme information for a question"""
        # Get the question object with consultation in one query
        question = self.get_object()

        # Get all themes for this question
        themes = models.SelectedTheme.objects.filter(question=question).values(
            "id", "name", "description"
        )

        serializer = ThemeInformationSerializer(data={"themes": list(themes)})
        serializer.is_valid()

        return Response(serializer.data)


class BespokeResultsSetPagination(PageNumberPagination):
    # TODO: remove this, and adapt .js to mach standard PageNumberPagination
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        original = super().get_paginated_response(data).data

        if question_id := self.request._request.GET.get("question_id"):
            respondents_total = models.Response.objects.filter(question_id=question_id).count()
        else:
            respondents_total = None

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
        consultation_uuid = self.kwargs["consultation_pk"]
        queryset = models.Response.objects.filter(question__consultation_id=consultation_uuid)

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
    def demographic_aggregations(self, request, consultation_pk=None):
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
    def theme_aggregations(self, request, consultation_pk=None):
        """Get theme aggregations for filtered responses"""

        # Get theme counts from the filtered responses
        theme_counts = (
            models.SelectedTheme.objects.filter(
                responseannotation__response__in=self.get_queryset(),
                responseannotation__response__question__has_free_text__isnull=False,
            )
            .values("id")
            .annotate(count=Count("responseannotation", distinct=True))
        )

        theme_aggregations = {str(theme["id"]): theme["count"] for theme in theme_counts}

        serializer = ThemeAggregationsSerializer(data={"theme_aggregations": theme_aggregations})
        serializer.is_valid()

        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="toggle-flag")
    def toggle_flag(self, request, consultation_pk=None, pk=None):
        """Toggle flag on/off for the user"""
        response = self.get_object()
        if response.annotation.flagged_by.contains(request.user):
            response.annotation.flagged_by.remove(request.user)
        else:
            response.annotation.flagged_by.add(request.user)
        response.annotation.save()
        return Response()


class UserViewSet(ModelViewSet):
    def create(self, request, *args, **kwargs):
        # Support both single and bulk creation
        data = request.data
        has_dashboard_access = data.get("has_dashboard_access", False)

        # If 'emails' is present and is a list, treat as bulk creation
        if isinstance(data.get("emails"), list):
            emails = data["emails"]
            created_users = []
            errors = []
            for email in emails:
                serializer = self.get_serializer(
                    data={"email": email, "has_dashboard_access": has_dashboard_access}
                )
                if serializer.is_valid():
                    user = serializer.save()
                    created_users.append(user)
                else:
                    errors.append({"email": email, "errors": serializer.errors})
            if errors:
                return Response({"detail": "Some users not created.", "errors": errors}, status=400)
            return Response(self.get_serializer(created_users, many=True).data, status=201)

        # Otherwise, treat as single user creation using default DRF behavior
        return super().create(request, *args, **kwargs)

    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = PageNumberPagination
    queryset = models.User.objects.all()


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


@api_view(["GET"])
def get_git_sha(_request) -> Response:
    return Response({"sha": settings.GIT_SHA})
