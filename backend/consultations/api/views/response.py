from django.db.models import Exists, OuterRef
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultations import models
from consultations.api.filters import ResponseFilter, ResponseSearchFilter
from consultations.api.permissions import (
    CanSeeConsultation,
)
from consultations.api.serializers import (
    ResponseSerializer,
    ResponseThemeInformationSerializer,
    ThemeSerializer,
)


class BespokeResultsSetPagination(PageNumberPagination):
    # TODO: remove this, and adapt .js to match standard PageNumberPagination
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_page_size(self, request):
        search_mode = request.query_params.get("searchMode")

        if search_mode == "representative":
            # We only want to return top 10 representative responses
            return min(10, self.max_page_size)
        else:
            return super().get_page_size(request)

    def get_paginated_response(self, data):
        original = super().get_paginated_response(data).data

        if hasattr(self, "_question_respondents_total"):
            respondents_total = self._question_respondents_total
        elif question_id := (
            self.request._request.resolver_match.kwargs.get("question_pk")
            or self.request._request.GET.get("question_id")
        ):
            respondents_total = models.Response.objects.filter(question_id=question_id).count()
            self._question_respondents_total = respondents_total
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
    permission_classes = [IsAuthenticated, CanSeeConsultation]
    pagination_class = BespokeResultsSetPagination
    filter_backends = [ResponseSearchFilter, DjangoFilterBackend]
    filterset_class = ResponseFilter
    http_method_names = ["get", "patch", "post"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        queryset = models.Response.objects.filter(question__consultation_id=consultation_uuid)

        # Support nesting under questions: /questions/{question_pk}/responses/
        question_pk = self.kwargs.get("question_pk")
        if question_pk:
            queryset = queryset.filter(question_id=question_pk)

        # Optimize queryset with select_related and prefetch_related
        queryset = queryset.select_related(
            "respondent",
            "annotation",
            "question",
        ).prefetch_related(
            "chosen_options",
            "respondent__demographics",
            "annotation__responseannotationtheme_set__assigned_by",
            "annotation__responseannotationtheme_set",
            "annotation__responseannotationtheme_set__theme",
        )

        queryset = queryset.annotate(
            is_flagged=Exists(
                models.ResponseAnnotation.objects.filter(
                    response=OuterRef("pk"), flagged_by=self.request.user
                )
            ),
            is_read_by_user=Exists(
                models.Response.objects.filter(read_by=self.request.user, pk=OuterRef("pk"))
            ),
            annotation_is_edited=Exists(
                models.ResponseAnnotation.history.filter(id=OuterRef("annotation__id")).values(
                    "id"
                )[1:]
            ),
            annotation_has_human_assigned_themes=Exists(
                models.ResponseAnnotationTheme.history.filter(
                    response_annotation_id=OuterRef("annotation__id"),
                    assigned_by__isnull=False,
                )
            ),
        )
        # Apply additional FilterSet filtering (including themeFilters)
        filterset = self.filterset_class(self.request.GET, queryset=queryset, request=self.request)
        qs = filterset.qs
        # Only use .distinct() when filters that JOIN through M2M are active —
        # these can produce duplicate rows.
        if (
            self.request.GET.get("themeFilters")
            or self.request.GET.get("demographics")
            or self.request.GET.get("multiple_choice_answer")
        ):
            qs = qs.distinct()
        return qs

    @action(
        detail=True,
        methods=["get"],
        url_path="themes",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def themes(self, request, consultation_pk=None, pk=None):
        """Get themes for given responses"""
        response = self.get_object()

        all_themes = models.SelectedTheme.objects.filter(question=response.question)
        if response.question.consultation.display_ai_selected_themes:
            annotation, _ = models.ResponseAnnotation.objects.get_or_create(response=response)
            selected_themes = annotation.themes.all()
        else:
            selected_themes = []

        # Serialize the themes properly using ThemeSerializer
        all_themes_data = ThemeSerializer(all_themes, many=True).data
        selected_themes_data = ThemeSerializer(selected_themes, many=True).data

        serializer = ResponseThemeInformationSerializer(
            data={"selected_themes": selected_themes_data, "all_themes": all_themes_data}
        )
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        url_path="toggle-flag",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def toggle_flag(self, request, consultation_pk=None, pk=None):
        """Toggle flag on/off for the user"""
        response = self.get_object()
        if response.annotation.flagged_by.contains(request.user):
            response.annotation.flagged_by.remove(request.user)
        else:
            response.annotation.flagged_by.add(request.user)
        response.annotation.save()
        return Response()

    @action(
        detail=True,
        methods=["post"],
        url_path="mark-read",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def mark_read(self, request, consultation_pk=None, pk=None):
        """Mark this response as read by the current user"""
        response = self.get_object()

        # Check if already read before marking
        was_already_read = response.is_read_by(request.user)
        response.mark_as_read_by(request.user)

        return Response(
            {
                "message": "Response marked as read",
                "was_already_read": was_already_read,
            }
        )
