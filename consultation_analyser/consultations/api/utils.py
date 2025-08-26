from collections import defaultdict
from typing import TypedDict

from django.db.models import Count, Q, QuerySet
from pgvector.django import CosineDistance

from ...embeddings import embed_text
from ..models import DemographicOption


class FilterParams(TypedDict, total=False):
    theme_list: list[str]
    search_mode: str
    demo_filters: dict[str, list[str]]
    search_value: str


def parse_filters_from_serializer(validated_data: dict) -> FilterParams:
    """Parse filter parameters from serializer validated data"""
    filters = FilterParams()

    if "searchValue" in validated_data:
        filters["search_value"] = validated_data["searchValue"]

    if "searchMode" in validated_data:
        filters["search_mode"] = validated_data["searchMode"]

    # Parse demographic filters
    demo_filters = validated_data.get("demoFilters", [])
    if demo_filters:
        filters_dict = defaultdict(list)
        for filter_str in demo_filters:
            if ":" in filter_str:
                key, value = filter_str.split(":", 1)
                if key and value:
                    filters_dict[key].append(value)
        if filters_dict:
            filters["demo_filters"] = dict(filters_dict)

    return filters


def safe_json_encode(txt: str):
    """try and cast a bool or str to json, anything else will be a string"""
    if txt.lower() == "true":
        return True
    if txt.lower() == "false":
        return False
    return txt


def build_response_filter_query(filters: FilterParams) -> Q:
    """Build a Q object for filtering responses based on filter params"""
    query = Q()

    # Handle demographic filters
    if demo_filters := filters.get("demo_filters"):
        for field, values in demo_filters.items():
            json_values = list(map(safe_json_encode, values))
            demographics = DemographicOption.objects.filter(
                field_name=field, field_value__in=json_values
            )
            query &= Q(respondent__demographics__in=demographics)

    return query


def get_filtered_responses_with_themes(
    queryset: QuerySet,
    filters: FilterParams | None = None,
):
    """Single optimized query to get all filtered responses with their themes"""
    response_filter = build_response_filter_query(filters or {})
    queryset = (
        queryset.filter(response_filter)
        .select_related("respondent", "annotation")
        .prefetch_related("annotation__themes")
        .only(
            # Response fields
            "id",
            "respondent_id",
            "question_id",
            "free_text",
            "created_at",
            # Respondent fields
            "respondent__id",
            "respondent__themefinder_id",
            "respondent__demographics",
            # Annotation fields
            "annotation__id",
            "annotation__sentiment",
            "annotation__evidence_rich",
        )
        .defer("embedding", "search_vector")
    )


    if filters and filters.get("search_value"):
        if filters.get("search_mode") == "semantic":
            # semantic_distance: exact match = 0, exact opposite = 2
            embedded_query = embed_text(filters["search_value"])
            distance = CosineDistance("embedding", embedded_query)
            return queryset.annotate(distance=distance).order_by("distance")
        else:
            return queryset.filter(free_text__icontains=filters["search_value"])

    return queryset.order_by("created_at")  # Consistent ordering for pagination
