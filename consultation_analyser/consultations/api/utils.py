from typing import TypedDict

from django.db.models import Count, Q, QuerySet
from pgvector.django import CosineDistance

from ...embeddings import embed_text


class FilterParams(TypedDict, total=False):
    sentiment_list: list[str]
    theme_list: list[str]
    evidence_rich: bool
    search_mode: str
    demo_filters: dict[str, str]
    search_value: str


def parse_filters_from_serializer(validated_data: dict) -> FilterParams:
    """Parse filter parameters from serializer validated data"""
    filters = FilterParams()

    sentiment_filters = validated_data.get("sentimentFilters", "")
    if sentiment_filters:
        filters["sentiment_list"] = sentiment_filters.split(",")

    theme_filters = validated_data.get("themeFilters", "")
    if theme_filters:
        filters["theme_list"] = theme_filters.split(",")

    if validated_data.get("evidenceRich"):
        filters["evidence_rich"] = True

    if "searchValue" in validated_data:
        filters["search_value"] = validated_data["searchValue"]

    if "searchMode" in validated_data:
        filters["search_mode"] = validated_data["searchMode"]

    # Parse demographic filters
    demo_filters = validated_data.get("demoFilters", [])
    if demo_filters:
        filters_dict = {}
        for filter_str in demo_filters:
            if ":" in filter_str:
                key, value = filter_str.split(":", 1)
                if key and value:
                    filters_dict[key] = value
        if filters_dict:
            filters["demo_filters"] = filters_dict

    return filters


def build_response_filter_query(filters: FilterParams) -> Q:
    """Build a Q object for filtering responses based on filter params"""
    query = Q()

    if filters.get("sentiment_list"):
        query &= Q(annotation__sentiment__in=filters["sentiment_list"])

    if evidence_rich := filters.get("evidence_rich"):
        query &= Q(annotation__evidence_rich=evidence_rich)

    # Handle demographic filters
    if demo_filters := filters.get("demo_filters"):
        for field, value in demo_filters.items():
            field_query = Q()
            # Handle boolean values
            if value.lower() in ["true", "false"]:
                bool_value = value.lower() == "true"
                field_query |= Q(**{f"respondent__demographics__{field}": bool_value})
            else:
                # Handle string values
                field_query |= Q(**{f"respondent__demographics__{field}": value})
            query &= field_query

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

    if filters and filters.get("theme_list"):
        theme_ids = filters["theme_list"]
        # Use single JOIN with HAVING clause for AND logic
        queryset = (
            queryset.filter(annotation__themes__id__in=theme_ids)
            .annotate(matched_theme_count=Count("annotation__themes", distinct=True))
            .filter(matched_theme_count=len(theme_ids))
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
