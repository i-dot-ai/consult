from collections import defaultdict

from django.db.models import Count, Exists, OuterRef
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultation_analyser.consultations import models
from consultation_analyser.consultations.api.filters import HybridSearchFilter, ResponseFilter
from consultation_analyser.consultations.api.permissions import (
    CanSeeConsultation,
    HasDashboardAccess,
)
from consultation_analyser.consultations.api.serializers import (
    DemographicAggregationsSerializer,
    ResponseSerializer,
    ThemeAggregationsSerializer,
)


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
