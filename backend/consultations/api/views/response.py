from collections import defaultdict
from time import time

from django.conf import settings
from django.db.models import BooleanField, Case, Count, Exists, OuterRef, Value, When
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
    DemographicAggregationsSerializer,
    ResponseSerializer,
    ResponseThemeInformationSerializer,
    ThemeAggregationsSerializer,
    ThemeSerializer,
)

logger = settings.LOGGER


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
    
    def list(self, request, *args, **kwargs):
        """Override list to add performance logging"""
        start_time = time()
        consultation_pk = kwargs.get('consultation_pk')
        
        response = super().list(request, *args, **kwargs)
        
        duration_ms = int((time() - start_time) * 1000)
        result_count = response.data.get('filtered_total', 0) if isinstance(response.data, dict) else len(response.data)
        
        logger.info(
            "Response list completed in {duration_ms}ms for consultation {consultation_id} with {result_count} results",
            duration_ms=duration_ms,
            consultation_id=str(consultation_pk),
            result_count=result_count,
        )
        
        return response

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
            # CRITICAL PERFORMANCE: History table queries are extremely expensive
            # The annotation is considered edited if:
            # 1. It has human-assigned themes (most common case)
            # 2. OR it has been reviewed (reviewed_by is set)
            # 3. OR it has been flagged by anyone (flagged_by has entries)
            # This covers all meaningful edit scenarios without history queries
            annotation_is_edited=Case(
                # Check for human-assigned themes
                When(
                    Exists(
                        models.ResponseAnnotationTheme.objects.filter(
                            response_annotation_id=OuterRef("annotation__id"),
                            assigned_by__isnull=False,
                        )
                    ),
                    then=Value(True)
                ),
                # Check if annotation has been reviewed
                When(
                    Exists(
                        models.ResponseAnnotation.objects.filter(
                            id=OuterRef("annotation__id"),
                            reviewed_by__isnull=False,
                        )
                    ),
                    then=Value(True)
                ),
                # Check if annotation has been flagged
                When(
                    Exists(
                        models.ResponseAnnotation.flagged_by.through.objects.filter(
                            responseannotation_id=OuterRef("annotation__id")
                        )
                    ),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
            annotation_has_human_assigned_themes=Exists(
                models.ResponseAnnotationTheme.objects.filter(
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
        start_time = time()
        
        # More efficient: get respondent IDs from filtered responses, then aggregate demographics
        filtered_respondent_ids = self.get_queryset().values_list('respondent_id', flat=True).distinct()
        respondent_count = len(list(filtered_respondent_ids))
        
        aggregations = (
            models.DemographicOption.objects.filter(
                respondent__id__in=filtered_respondent_ids
            )
            .values("field_name", "field_value")
            .annotate(count=Count("respondent", distinct=True))
        )

        result = defaultdict(dict)
        for item in aggregations:
            result[item["field_name"]][item["field_value"]] = item["count"]

        serializer = DemographicAggregationsSerializer(data={"demographic_aggregations": result})
        serializer.is_valid()
        
        duration_ms = int((time() - start_time) * 1000)
        logger.info(
            "Demographic aggregations completed in {duration_ms}ms for consultation {consultation_id} with {respondent_count} respondents and {field_count} fields",
            duration_ms=duration_ms,
            consultation_id=str(consultation_pk),
            respondent_count=respondent_count,
            field_count=len(result),
        )

        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="theme-aggregations",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def theme_aggregations(self, request, consultation_pk=None):
        """Get theme aggregations for filtered responses"""
        start_time = time()

        # More efficient query: aggregate themes directly from ResponseAnnotationTheme
        # instead of joining through SelectedTheme
        filtered_response_ids = self.get_queryset().values_list('id', flat=True)
        response_count = len(list(filtered_response_ids))
        
        theme_counts = (
            models.ResponseAnnotationTheme.objects.filter(
                response_annotation__response_id__in=filtered_response_ids,
                response_annotation__response__question__has_free_text=True,
            )
            .values("theme_id")
            .annotate(count=Count("response_annotation", distinct=True))
        )

        theme_aggregations = {str(theme["theme_id"]): theme["count"] for theme in theme_counts}

        serializer = ThemeAggregationsSerializer(data={"theme_aggregations": theme_aggregations})
        serializer.is_valid()
        
        duration_ms = int((time() - start_time) * 1000)
        logger.info(
            "Theme aggregations completed in {duration_ms}ms for consultation {consultation_id} with {response_count} responses and {theme_count} themes",
            duration_ms=duration_ms,
            consultation_id=str(consultation_pk),
            response_count=response_count,
            theme_count=len(theme_aggregations),
        )

        return Response(serializer.data)

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
