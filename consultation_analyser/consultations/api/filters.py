from collections import defaultdict

from django.db.models import Count
from django_filters.rest_framework import BaseInFilter, BooleanFilter, CharFilter, FilterSet
from pgvector.django import CosineDistance
from rest_framework.filters import SearchFilter

from consultation_analyser.consultations.models import Response
from consultation_analyser.embeddings import embed_text


def safe_json_encode(txt: str):
    """cast to a bool or str"""
    match txt.lower():
        case "true":
            return True
        case "false":
            return False
        case _:
            return txt


class ResponseFilter(FilterSet):
    # TODO: adjust the frontend to match sensible DRF defaults
    sentimentFilters = BaseInFilter(field_name="annotation__sentiment", lookup_expr="in")
    evidenceRich = BooleanFilter(field_name="annotation__evidence_rich")
    themeFilters = BaseInFilter(method="filter_themes")
    demoFilters = CharFilter(method="filter_demographics")
    is_flagged = BooleanFilter()

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

    def filter_demographics(self, queryset, name, value):
        demo_filters = self.data.getlist("demoFilters")
        if not demo_filters:
            return queryset

        filter_dict = defaultdict(list)
        for filter_str in demo_filters:
            if ":" in filter_str:
                key, value = filter_str.split(":", 1)
                filter_dict[key].append(value)

        for key, values in filter_dict.items():
            python_values = list(map(safe_json_encode, values))
            queryset = queryset.filter(
                respondent__demographics__field_name=key,
                respondent__demographics__field_value__in=python_values,
            )
        return queryset

    class Meta:
        model = Response
        fields = [
            "respondent_id",
        ]


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
