from django.db.models import Count
from django_filters.rest_framework import BaseInFilter, BooleanFilter, FilterSet
from pgvector.django import CosineDistance
from rest_framework.filters import SearchFilter

from consultation_analyser.consultations.models import Response
from consultation_analyser.embeddings import embed_text


class ResponseFilter(FilterSet):
    # TODO: adjust the frontend to match sensible DRF defaults
    sentimentFilters = BaseInFilter(field_name="annotation__sentiment", lookup_expr="in")
    evidenceRich = BooleanFilter(field_name="annotation__evidence_rich")
    themeFilters = BaseInFilter(method="filter_themes", lookup_expr="in")
    demographics = BaseInFilter(field_name="respondent__demographics", lookup_expr="in")
    is_flagged = BooleanFilter()
    chosen_options = BaseInFilter(lookup_expr="in")

    def filter_themes(self, queryset, name, value):
        if not value:
            return queryset
        # Use single JOIN with HAVING clause for AND logic
        qs = (
            queryset.filter(annotation__themes__id__in=value)
            .annotate(matched_theme_count=Count("annotation__themes", distinct=True))
            .filter(matched_theme_count=len(value))
        )
        return qs

    class Meta:
        model = Response
        fields = ["respondent_id", "chosen_options"]


class HybridSearchFilter(SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_value = request.query_params.get("searchValue")
        if not search_value:
            return queryset

        if request.query_params.get("searchMode") == "semantic":
            # semantic_distance: exact match = 0, exact opposite = 2
            embedded_query = embed_text(search_value)
            distance = CosineDistance("embedding", embedded_query)
            return queryset.annotate(distance=distance).order_by("distance")
        else:
            return queryset.filter(free_text__icontains=search_value)
