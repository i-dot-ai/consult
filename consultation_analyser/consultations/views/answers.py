from collections import defaultdict
from datetime import datetime
from logging import getLogger
from typing import Literal, TypedDict
from uuid import UUID

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from pgvector.django import CosineDistance

from ...embeddings import embed_text
from .. import models
from .decorators import user_can_see_consultation, user_can_see_dashboards

logger = getLogger(__file__)


class DataDict(TypedDict):
    all_respondents: list
    has_more_pages: bool
    respondents_total: int
    filtered_total: int
    theme_mappings: list
    demographic_options: dict[str, list[str]]
    demographic_aggregations: dict[str, dict[str, int]]


class FilterParams(TypedDict, total=False):
    sentiment_list: list[str]
    theme_list: list[str]
    evidence_rich: bool
    search_mode: Literal["semantic", "keyword"]
    demo_filters: dict[str, str]
    search_value: str
    themes_sort_type: str  # "frequency" or "alphabetical"
    themes_sort_direction: str  # "ascending" or "descending"


def parse_filters_from_request(request: HttpRequest) -> FilterParams:
    """Parse filter parameters from request GET params"""
    filters = FilterParams()

    sentiment_filters = request.GET.get("sentimentFilters", "")
    if sentiment_filters:
        filters["sentiment_list"] = sentiment_filters.split(",")

    theme_filters = request.GET.get("themeFilters", "")
    if theme_filters:
        filters["theme_list"] = theme_filters.split(",")

    themes_sort_direction = request.GET.get("themesSortDirection", "")
    if themes_sort_direction in ["ascending", "descending"]:
        filters["themes_sort_direction"] = themes_sort_direction

    themes_sort_type = request.GET.get("themesSortType", "")
    if themes_sort_type in ["frequency", "alphabetical"]:
        filters["themes_sort_type"] = themes_sort_type

    evidence_rich_filter = request.GET.get("evidenceRich")
    if evidence_rich_filter:
        filters["evidence_rich"] = True

    search_value = request.GET.get("searchValue")
    if search_value:
        filters["search_value"] = search_value

    search_mode = request.GET.get("searchMode")
    if search_mode:
        if search_mode not in ("semantic", "keyword"):
            raise ValidationError("search mode must be one of semantic, keyword")
        filters["search_mode"] = search_mode

    # Expected format - `demoFilters=age:18&demoFilters=country:england`
    demo_filters = request.GET.getlist("demoFilters")

    def split(txt):
        # ignores consecutive colons
        # TODO: remove this in favour of DRF
        return tuple(filter(None, txt.split(":")))

    if demo_filters:
        filters_dict = dict(map(split, demo_filters))
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
    demo_filters = filters.get("demo_filters")
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
    question: models.Question,
    filters: FilterParams | None = None,
):
    """Single optimized query to get all filtered responses with their themes"""
    response_filter = build_response_filter_query(filters or {}, question)
    queryset = (
        models.Response.objects.filter(response_filter)
        .select_related("respondent", "annotation")
        .prefetch_related("annotation__themes")
        .only(
            # Response fields
            "id",
            "respondent_id",
            "question_id",
            "free_text",
            "chosen_options",
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
        search_query = SearchQuery(filters["search_value"])

        if filters.get("search_mode") == "semantic":
            # semantic_distance: exact match = 0, exact opposite = 2
            embedded_query = embed_text(filters["search_value"])
            distance = CosineDistance("embedding", embedded_query)
            return queryset.annotate(distance=distance).order_by("distance")
        else:
            # term_frequency: exact match = 1+, no match = 0
            # normalization = 1: divides the rank by 1 + the logarithm of the document length
            distance = SearchRank("search_vector", search_query, normalization=1)
            return (
                queryset.filter(search_vector=search_query)
                .annotate(distance=distance)
                .order_by("-distance")
            )

    return queryset.order_by("created_at")  # Consistent ordering for pagination


def get_theme_summary_optimized(
    question: models.Question,
    filtered_responses: QuerySet | None = None,
    themes_sort_type: str | None = None,
    themes_sort_direction: str | None = None,
) -> list[dict]:
    """Database-optimized theme aggregation - shows all themes in filtered responses"""
    # Empty queryset would be valid, explicitly check for None
    if filtered_responses is None:
        filtered_responses = models.Response.objects.filter(question=question)

    # Ordering of responses - default to order by frequency, descengind
    order_by_field_name = "response_count"
    direction = "-"
    if themes_sort_type == "alphabetical":
        order_by_field_name = "name"
    if themes_sort_direction == "ascending":
        direction = ""

    # Now get all themes that appear in those filtered responses
    # This shows ALL themes that appear in responses matching the filter criteria
    theme_data = (
        models.Theme.objects.filter(responseannotation__response__in=filtered_responses)
        .annotate(response_count=Count("responseannotation__response"))
        .values("id", "name", "description", "response_count")
        .order_by(f"{direction}{order_by_field_name}")
    )

    return [
        {
            "theme__id": theme["id"],
            "theme__name": theme["name"],
            "theme__description": theme["description"],
            "count": theme["response_count"],
        }
        for theme in theme_data
    ]


def build_respondent_data(response: models.Response) -> dict:
    """Extract respondent data building to separate function"""
    data = {
        "identifier": str(response.respondent.identifier),
        "free_text_answer_text": response.free_text or "",
        "demographic_data": response.respondent.demographics or {},
        "themes": [],
        "multiple_choice_answer": response.chosen_options or [],
        "evidenceRich": False,
    }

    if hasattr(response, "annotation") and response.annotation:
        annotation = response.annotation

        if annotation.evidence_rich == models.ResponseAnnotation.EvidenceRich.YES:
            data["evidenceRich"] = True

        # Add themes (already prefetched)
        data["themes"] = [
            {
                "id": theme.id,
                "name": theme.name,
                "description": theme.description,
            }
            for theme in annotation.themes.all()
        ]

    return data


def get_demographic_options(consultation: models.Consultation) -> dict[str, list]:
    """Get all demographic fields and their possible values from normalized storage"""
    options = (
        models.DemographicOption.objects.filter(consultation=consultation)
        .values_list("field_name", "field_value")
        .order_by("field_name", "field_value")
    )

    result = {}  # type: ignore[var-annotated]
    for field_name, field_value in options:
        if field_name not in result:
            result[field_name] = []
        result[field_name].append(field_value)

    return result


def derive_option_summary_from_responses(responses) -> list[dict]:
    """Get a summary of the selected options for a multiple choice question from response queryset"""
    option_counts = {}  # type: ignore[var-annotated]
    for response in responses:
        if response.chosen_options:
            for option in response.chosen_options:
                option_counts[option] = option_counts.get(option, 0) + 1

    return [option_counts] if option_counts else []


def get_demographic_aggregations_from_responses(filtered_respondents) -> dict[str, dict[str, int]]:
    """Aggregate demographic data for filtered responses using efficient database queries"""
    respondent_ids = filtered_respondents.values_list("respondent_id", flat=True).distinct()

    # Fetch all demographic data for these respondents in one query
    respondents_data = models.Respondent.objects.filter(id__in=respondent_ids).values_list(
        "demographics", flat=True
    )

    # Aggregate in memory (much faster than nested loops)
    aggregations: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for demographics in respondents_data:
        if demographics:
            for field_name, field_value in demographics.items():
                value_str = str(field_value)
                aggregations[field_name][value_str] += 1

    return {field: dict(counts) for field, counts in aggregations.items()}


@user_can_see_dashboards
@user_can_see_consultation
def question_responses_json(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    # Get the question object with consultation in one query
    question = get_object_or_404(
        models.Question.objects.select_related("consultation"),
        slug=question_slug,
        consultation__slug=consultation_slug,
    )

    # Parse filters from request
    filters = parse_filters_from_request(request)

    # Get respondents with their filtered responses and produce a lightweight respondent queryset
    full_qs = get_filtered_responses_with_themes(question, filters)
    respondent_qs = full_qs.only("id", "respondent_id")

    # Efficient counting using database aggregation
    filtered_total = respondent_qs.count()
    all_respondents_count = models.Response.objects.filter(question=question).count()

    # Get demographic options for this consultation
    demographic_options = get_demographic_options(question.consultation)

    # Get demographic aggregations for filtered responses
    demographic_aggregations = get_demographic_aggregations_from_responses(respondent_qs)

    # Generate theme mappings
    theme_mappings = []
    themes_sort_type = filters.get("themes_sort_type")
    themes_sort_direction = filters.get("themes_sort_direction")
    if question.has_free_text:
        # Generate theme mappings using optimized database query
        theme_data = get_theme_summary_optimized(
            question=question,
            filtered_responses=respondent_qs,
            themes_sort_type=themes_sort_type,
            themes_sort_direction=themes_sort_direction,
        )
        theme_mappings = [
            {
                "value": str(theme.get("theme__id", "")),
                "label": theme.get("theme__name", ""),
                "description": theme.get("theme__description", ""),
                "count": str(theme.get("count", 0)),
            }
            for i, theme in enumerate(theme_data)
        ]

    # Pagination
    DEFAULT_PAGE_SIZE = 50
    DEFAULT_PAGE = 1
    page_size = request.GET.get("page_size", DEFAULT_PAGE_SIZE)
    page_num = request.GET.get("page", DEFAULT_PAGE)

    # Use Django's lazy pagination - avoids counting all results
    paginator = Paginator(full_qs, page_size, allow_empty_first_page=True)
    page_obj = paginator.page(page_num)
    page_qs = page_obj.object_list

    # Only count when necessary (first page or when specifically needed)
    if page_num == DEFAULT_PAGE:
        filtered_total = respondent_qs.count()
    else:
        # For other pages, use paginator's optimized count
        filtered_total = paginator.count

    data: DataDict = {
        "all_respondents": [build_respondent_data(r) for r in page_qs],
        "has_more_pages": page_obj.has_next(),
        "respondents_total": all_respondents_count,
        "filtered_total": filtered_total,
        "theme_mappings": theme_mappings,
        "demographic_options": demographic_options,
        "demographic_aggregations": demographic_aggregations,
    }

    return JsonResponse(data)


@user_can_see_dashboards
@user_can_see_consultation
def index(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    # Get question data
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(
        models.Question,
        slug=question_slug,
        consultation=consultation,
    )

    """Simplified index that just renders the template - all data loaded via AJAX"""
    # Minimal context - all dynamic data loaded via respondents_json
    context = {
        "consultation_name": consultation.title,
        "consultation_slug": consultation_slug,
        "question": question,
        "question_slug": question_slug,
        "free_text_question_part": question if question.has_free_text else None,
        "has_multiple_choice_question_part": question.has_multiple_choice,
        "selected_theme_mappings": [],  # Empty - loaded via AJAX
        "csv_button_data": [],  # Empty - loaded via AJAX
        "multiple_choice_summary": [],  # Empty - loaded via AJAX
        "stance_options": models.ResponseAnnotation.Sentiment.names,
        "has_individual_data": False,  # Shouldn't use this, demographic filters work more generally
    }

    return render(request, "consultations/answers/index.html", context)


@user_can_see_consultation
def show(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
    response_id: UUID,
):
    # Allow user to review and update theme mappings for a response.
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)
    response = get_object_or_404(models.Response, id=response_id, question=question)

    # Get or create annotation for this response
    annotation, _ = models.ResponseAnnotation.objects.get_or_create(response=response)

    # Get all themes for this question
    all_themes = models.Theme.objects.filter(question=question)

    # Get existing themes for this response
    existing_themes = annotation.themes.all().values_list("id", flat=True)

    if request.method == "POST":
        requested_themes = request.POST.getlist("theme")

        # Set human-reviewed themes (preserves original AI assignments)
        if requested_themes:
            themes_to_add = models.Theme.objects.filter(id__in=requested_themes, question=question)
            annotation.set_human_reviewed_themes(themes_to_add, request.user)
        else:
            # No themes selected - clear human-reviewed assignments
            annotation.set_human_reviewed_themes([], request.user)

        # Mark as human reviewed
        annotation.mark_human_reviewed(request.user)

        return redirect(
            "show_next_response", consultation_slug=consultation_slug, question_slug=question_slug
        )

    elif request.method == "GET":
        context = {
            "consultation_name": consultation.title,
            "consultation_slug": consultation_slug,
            "question": question,
            "response": response,
            "all_themes": list(all_themes),
            "existing_themes": list(existing_themes),
            "date_created": datetime.strftime(response.created_at, "%d %B %Y"),
        }

        return render(request, "consultations/answers/show.html", context)


@user_can_see_consultation
def show_next(request: HttpRequest, consultation_slug: str, question_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)

    def handle_no_responses():
        context = {
            "consultation_name": consultation.title,
            "consultation_slug": consultation_slug,
            "question": question,
        }
        return render(request, "consultations/answers/no_responses.html", context)

    # Check if this question has free text (only free text questions have themes)
    if not question.has_free_text:
        return handle_no_responses()

    # Get the next response that has not been human reviewed
    # Left join with annotation to find responses without annotations or not reviewed
    next_response = (
        models.Response.objects.filter(
            question=question,
            free_text__isnull=False,  # Only responses with free text
            free_text__gt="",  # Non-empty free text
        )
        .exclude(
            annotation__human_reviewed=True  # Exclude already reviewed
        )
        .order_by("?")
        .first()
    )

    if next_response:
        return redirect(
            "show_response",
            consultation_slug=consultation_slug,
            question_slug=question_slug,
            response_id=next_response.id,
        )

    return handle_no_responses()
