from datetime import datetime
from typing import TypedDict
from uuid import UUID

from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .. import models
from .decorators import user_can_see_consultation, user_can_see_dashboards


class DataDict(TypedDict):
    all_respondents: list
    has_more_pages: bool
    respondents_total: int
    filtered_total: int
    theme_mappings: list
    demographic_options: dict[str, list[str]]


class FilterParams(TypedDict, total=False):
    sentiment_list: list[str]
    theme_list: list[str]
    evidence_rich: bool
    search_value: str
    demographic_filters: dict[
        str, list[str]
    ]  # e.g. {"individual": ["true"], "region": ["north", "south"]}


def parse_filters_from_request(request: HttpRequest) -> FilterParams:
    """Parse filter parameters from request GET params"""
    filters = FilterParams()

    sentiment_filters = request.GET.get("sentimentFilters", "")
    if sentiment_filters:
        filters["sentiment_list"] = sentiment_filters.split(",")

    theme_filters = request.GET.get("themeFilters", "")
    if theme_filters:
        filters["theme_list"] = theme_filters.split(",")

    evidence_rich_filter = request.GET.get("evidenceRichFilter")
    if evidence_rich_filter == "evidence-rich":
        filters["evidence_rich"] = True

    search_value = request.GET.get("searchValue")
    if search_value:
        filters["search_value"] = search_value

    # Parse demographic filters
    # Expected format: demographicFilters[field]=value1,value2
    demographic_filters = {}
    for key in request.GET:
        if key.startswith("demographicFilters[") and key.endswith("]"):
            field_name = key[19:-1]  # Extract field name from demographicFilters[fieldname]
            values = request.GET.get(key, "").split(",")
            if values and values[0]:  # Only add if there are actual values
                demographic_filters[field_name] = values

    if demographic_filters:
        filters["demographic_filters"] = demographic_filters

    return filters


def build_response_filter_query(filters: FilterParams, question: models.Question) -> Q:
    """Build a Q object for filtering responses based on filter params"""
    query = Q(question=question)

    if filters.get("sentiment_list"):
        query &= Q(annotation__sentiment__in=filters["sentiment_list"])

    if filters.get("evidence_rich"):
        query &= Q(annotation__evidence_rich=models.ResponseAnnotation.EvidenceRich.YES)

    if filters.get("search_value"):
        query &= Q(free_text__icontains=filters["search_value"])

    # Handle demographic filters
    if filters.get("demographic_filters"):
        for field, values in filters["demographic_filters"].items():
            # Create a Q object that matches any of the values for this field
            field_query = Q()
            for value in values:
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
    question: models.Question, filters: FilterParams | None = None
):
    """Single optimized query to get all filtered responses with their themes"""
    response_filter = build_response_filter_query(filters or {}, question)
    queryset = (
        models.Response.objects.filter(response_filter)
        .select_related("respondent", "annotation")
        .prefetch_related("annotation__themes")
    )

    # Handle theme filtering with AND logic
    if filters and filters.get("theme_list"):
        # Create subqueries for each theme
        for theme_id in filters["theme_list"]:
            theme_exists = models.ResponseAnnotationTheme.objects.filter(
                response_annotation__response=OuterRef("pk"), theme_id=theme_id
            )
            queryset = queryset.filter(Exists(theme_exists))

    return queryset.distinct().order_by("created_at")  # Consistent ordering for pagination


def get_theme_summary_optimized(
    question: models.Question, filters: FilterParams | None = None
) -> list[dict]:
    """Database-optimized theme aggregation - shows all themes in filtered responses"""
    # Get the filtered responses using the same logic as get_filtered_responses_with_themes
    response_filter = build_response_filter_query(filters or {}, question)
    filtered_responses = models.Response.objects.filter(response_filter)

    # Apply theme filtering with AND logic if needed
    if filters and filters.get("theme_list"):
        # Create subqueries for each theme
        for theme_id in filters["theme_list"]:
            theme_exists = models.ResponseAnnotationTheme.objects.filter(
                response_annotation__response=OuterRef("pk"), theme_id=theme_id
            )
            filtered_responses = filtered_responses.filter(Exists(theme_exists))

    # Now get all themes that appear in those filtered responses
    # This shows ALL themes that appear in responses matching the filter criteria
    theme_data = (
        models.Theme.objects.filter(responseannotation__response__in=filtered_responses)
        .annotate(response_count=Count("responseannotation__response", distinct=True))
        .values("id", "name", "description", "response_count")
        .order_by("-response_count")
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


def build_respondent_data(respondent: models.Respondent, response: models.Response) -> dict:
    """Extract respondent data building to separate function"""
    data = {
        "id": f"response-{respondent.identifier}",
        "identifier": str(respondent.identifier),
        "sentiment_position": "",
        "free_text_answer_text": response.free_text or "",
        "demographic_data": respondent.demographics or {},
        "themes": [],
        "multiple_choice_answer": [response.chosen_options] if response.chosen_options else [],
        "evidenceRich": False,
        "individual": respondent.demographics.get("individual", False),
    }

    if hasattr(response, "annotation") and response.annotation:
        annotation = response.annotation

        if annotation.sentiment:
            data["sentiment_position"] = annotation.sentiment

        if annotation.evidence_rich == models.ResponseAnnotation.EvidenceRich.YES:
            data["evidenceRich"] = True

        # Add themes (already prefetched)
        data["themes"] = [
            {
                "id": theme.id,
                "stance": None,  # Stance is no longer stored in new models
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


@user_can_see_dashboards
@user_can_see_consultation
def question_responses_json(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    page_size = request.GET.get("page_size")
    page = request.GET.get("page", 1)

    # Get the question object with consultation in one query
    question = get_object_or_404(
        models.Question.objects.select_related("consultation"),
        slug=question_slug,
        consultation__slug=consultation_slug,
    )

    # Parse filters from request
    filters = parse_filters_from_request(request)

    # Generate theme mappings
    theme_mappings = []
    if question.has_free_text:
        # Generate theme mappings using optimized database query
        theme_data = get_theme_summary_optimized(question, filters)
        theme_mappings = [
            {
                "inputId": f"themesfilter-{i}",
                "value": str(theme.get("theme__id", "")),
                "label": theme.get("theme__name", ""),
                "description": theme.get("theme__description", ""),
                "count": str(theme.get("count", 0)),
            }
            for i, theme in enumerate(theme_data)
        ]

    # Get respondents with their filtered responses using the same logic as theme filtering
    # First get the filtered responses using AND logic for themes
    filtered_responses = get_filtered_responses_with_themes(question, filters)

    # Then get respondents who have these filtered responses
    filtered_respondents = (
        models.Respondent.objects.filter(response__in=filtered_responses)
        .prefetch_related(
            Prefetch(
                "response_set",
                queryset=filtered_responses.select_related("annotation").prefetch_related(
                    "annotation__themes"
                ),
                to_attr="filtered_responses",
            )
        )
        .distinct()
        .order_by("pk")
    )

    # Efficient counting using database aggregation
    filtered_total = filtered_respondents.count()
    all_respondents_count = models.Response.objects.filter(question=question).aggregate(
        count=Count("respondent_id", distinct=True)
    )["count"]

    # Get demographic options for this consultation
    demographic_options = get_demographic_options(question.consultation)

    data: DataDict = {
        "all_respondents": [],
        "has_more_pages": False,
        "respondents_total": all_respondents_count,
        "filtered_total": filtered_total,
        "theme_mappings": theme_mappings,
        "demographic_options": demographic_options,
    }

    # Pagination
    if page_size:
        pagination = Paginator(filtered_respondents, page_size)
        current_page = pagination.page(page)
        respondents = current_page.object_list
        data["has_more_pages"] = current_page.has_next()
    else:
        respondents = filtered_respondents

    # Build response data efficiently using prefetched data
    for respondent in respondents:
        # Use prefetched filtered_responses
        response = respondent.filtered_responses[0] if respondent.filtered_responses else None
        if not response:
            continue

        respondent_data = build_respondent_data(respondent, response)
        data["all_respondents"].append(respondent_data)

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
    # Check for individual data (lightweight query)
    has_individual_data = models.Respondent.objects.filter(
        consultation=consultation, demographics__has_key="individual"
    ).exists()

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
        "has_individual_data": has_individual_data,
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
