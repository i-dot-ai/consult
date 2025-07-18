from typing import TypedDict

from django.db.models import Q

from .. import models


class FilterParams(TypedDict, total=False):
    sentiment_list: list[str]
    theme_list: list[str]
    evidence_rich: bool
    search_mode: str
    demo_filters: dict[str, str]
    search_value: str
    themes_sort_type: str
    themes_sort_direction: str


def parse_filters_from_serializer(validated_data: dict) -> FilterParams:
    """Parse filter parameters from serializer validated data"""
    filters = FilterParams()
    
    sentiment_filters = validated_data.get("sentimentFilters", "")
    if sentiment_filters:
        filters["sentiment_list"] = sentiment_filters.split(",")
    
    theme_filters = validated_data.get("themeFilters", "")
    if theme_filters:
        filters["theme_list"] = theme_filters.split(",")
    
    if "themesSortDirection" in validated_data:
        filters["themes_sort_direction"] = validated_data["themesSortDirection"]
    
    if "themesSortType" in validated_data:
        filters["themes_sort_type"] = validated_data["themesSortType"]
    
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


def build_response_filter_query(filters: FilterParams, question: models.Question) -> Q:
    """Build a Q object for filtering responses based on filter params"""
    query = Q(question=question)
    
    if filters.get("sentiment_list"):
        query &= Q(annotation__sentiment__in=filters["sentiment_list"])
    
    if filters.get("evidence_rich"):
        query &= Q(annotation__evidence_rich=models.ResponseAnnotation.EvidenceRich.YES)
    
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