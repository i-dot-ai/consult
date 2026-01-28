from collections import defaultdict

from backend.consultations import models
from backend.consultations.api.filters import ResponseFilter, ResponseSearchFilter
from backend.consultations.api.permissions import (
    CanSeeConsultation,
)
from backend.consultations.api.serializers import (
    DemographicAggregationsSerializer,
    ResponseSerializer,
    ResponseThemeInformationSerializer,
    ThemeAggregationsSerializer,
    ThemeSerializer,
)
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


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

        # Get question_id count from the viewset if available, otherwise calculate once
        if hasattr(self, "_question_respondents_total"):
            respondents_total = self._question_respondents_total
        elif question_id := self.request._request.GET.get("question_id"):
            respondents_total = models.Response.objects.filter(question_id=question_id).count()
            # Cache it on the viewset for subsequent calls
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
        return filterset.qs.distinct()

    @action(
        detail=False,
        methods=["get"],
        url_path="demographic-aggregations",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
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

        serializer = DemographicAggregationsSerializer(data={"demographic_aggregations": result})
        serializer.is_valid()

        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="theme-aggregations",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
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

    @action(
        detail=True,
        methods=["get"],
        url_path="themes",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def themes(self, request, consultation_pk=None, pk=None):
        """Get themes for given responses"""
        response = get_object_or_404(models.Response, id=pk)
        question = response.question
        annotation, _ = models.ResponseAnnotation.objects.get_or_create(response=response)

        all_themes = models.SelectedTheme.objects.filter(question=question)
        selected_themes = annotation.themes.all()

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
