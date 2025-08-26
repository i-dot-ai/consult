from typing import TypedDict

from django.db.models import QuerySet
from pgvector.django import CosineDistance

from ...embeddings import embed_text


class FilterParams(TypedDict, total=False):
    search_mode: str
    search_value: str


def parse_filters_from_serializer(validated_data: dict) -> FilterParams:
    """Parse filter parameters from serializer validated data"""
    filters = FilterParams()

    if "searchValue" in validated_data:
        filters["search_value"] = validated_data["searchValue"]

    if "searchMode" in validated_data:
        filters["search_mode"] = validated_data["searchMode"]

    return filters


def get_filtered_responses_with_themes(
    queryset: QuerySet,
    filters: FilterParams | None = None,
):
    """Single optimized query to get all filtered responses with their themes"""
    queryset = (
        queryset.select_related("respondent", "annotation")
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
