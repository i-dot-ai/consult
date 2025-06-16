import hashlib
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
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
    demographic_filters: dict[str, list[str]]  # e.g. {"individual": ["true"], "region": ["north", "south"]}


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

    if filters.get("theme_list"):
        query &= Q(annotation__themes__id__in=filters["theme_list"])

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
    return (
        models.Response.objects.filter(response_filter)
        .select_related("respondent", "annotation")
        .prefetch_related("annotation__themes")
        .order_by("created_at")  # Consistent ordering for pagination
    )


def get_theme_summary_optimized(question: models.Question, filters: FilterParams | None = None) -> list[dict]:
    """Database-optimized theme aggregation - shows all themes in filtered responses"""
    # Get the filtered responses first
    response_filter = build_response_filter_query(filters or {}, question)
    filtered_responses = models.Response.objects.filter(response_filter)

    # Now get all themes that appear in those filtered responses
    # This shows ALL themes that appear in responses matching the filter criteria
    theme_data = (
        models.Theme.objects
        .filter(responseannotation__response__in=filtered_responses)
        .annotate(response_count=Count('responseannotation__response', distinct=True))
        .values('id', 'name', 'description', 'response_count')
        .order_by('-response_count')
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


def get_cached_theme_summary(question_id: str, filters_hash: str) -> list[dict] | None:
    """Get cached theme summary or None if not cached"""
    cache_key = f"theme_summary:{question_id}:{filters_hash}"
    return cache.get(cache_key)


def set_cached_theme_summary(question_id: str, filters_hash: str, data: list[dict], timeout: int = 300):
    """Cache theme summary for 5 minutes"""
    cache_key = f"theme_summary:{question_id}:{filters_hash}"
    cache.set(cache_key, data, timeout)


def get_filters_hash(filters: FilterParams) -> str:
    """Generate a hash for caching based on filter parameters"""
    return hashlib.md5(str(sorted(filters.items())).encode()).hexdigest() #nosec - not used for security


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
    options = models.DemographicOption.objects.filter(
        consultation=consultation
    ).values_list('field_name', 'field_value').order_by('field_name', 'field_value')

    result = {} # type: ignore[var-annotated]
    for field_name, field_value in options:
        if field_name not in result:
            result[field_name] = []
        result[field_name].append(field_value)

    return result


def derive_option_summary_from_responses(responses) -> list[dict]:
    """Get a summary of the selected options for a multiple choice question from response queryset"""
    option_counts = {} # type: ignore[var-annotated]
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
        consultation__slug=consultation_slug
    )

    # Parse filters from request
    filters = parse_filters_from_request(request)
    filters_hash = get_filters_hash(filters)

    # Generate theme mappings (disable cache temporarily for debugging)
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

    # Get respondents with their filtered responses using optimized query
    response_filter = build_response_filter_query(filters, question)
    filtered_respondents = (
        models.Respondent.objects
        .filter(response__in=models.Response.objects.filter(response_filter))
        .prefetch_related(
            Prefetch(
                'response_set',
                queryset=models.Response.objects.filter(response_filter)
                .select_related('annotation')
                .prefetch_related('annotation__themes'),
                to_attr='filtered_responses'
            )
        )
        .distinct()
        .order_by('pk')
    )

    # Efficient counting using database aggregation
    filtered_total = filtered_respondents.count()
    all_respondents_count = (
        models.Response.objects.filter(question=question)
        .aggregate(count=Count("respondent_id", distinct=True))["count"]
    )

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
    # Assume latest theme mappings i.e. from latest framework.
    consultation = get_object_or_404(models.ConsultationOld, slug=consultation_slug)
    question = get_object_or_404(models.QuestionOld, slug=question_slug, consultation=consultation)
    response = get_object_or_404(models.Answer, id=response_id)
    question_part = response.question_part

    all_theme_mappings_for_framework = models.ThemeMapping.get_latest_theme_mappings(question_part)

    latest_framework = (
        models.Framework.objects.filter(question_part=question_part).order_by("created_at").last()
    )
    all_themes = models.ThemeOld.objects.filter(
        framework=latest_framework
    )  # May include themes not mapped to anything

    existing_themes = all_theme_mappings_for_framework.filter(answer=response).values_list(
        "theme", flat=True
    )

    if request.method == "POST":
        requested_themes = request.POST.getlist("theme")
        existing_mappings = all_theme_mappings_for_framework.filter(answer=response).select_related(
            "theme"
        )

        # themes to delete
        existing_mappings.exclude(theme_id__in=requested_themes).delete()

        # themes to update to show set by human
        existing_mappings.filter(theme_id__in=requested_themes).exclude(
            user_audited=True,
        ).update(user_audited=True)

        # themes to add
        themes_to_add = set(requested_themes) - set(map(str, existing_themes))
        for theme_id in themes_to_add:
            models.ThemeMapping.objects.create(
                answer=response,
                theme_id=theme_id,
                user_audited=True,
            )  # From the theme we can infer it's from this framework

        # flag
        response.is_theme_mapping_audited = True
        response.save()

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
    consultation = get_object_or_404(models.ConsultationOld, slug=consultation_slug)
    question = get_object_or_404(models.QuestionOld, slug=question_slug, consultation=consultation)

    def handle_no_responses():
        context = {
            "consultation_name": consultation.title,
            "consultation_slug": consultation_slug,
            "question": question,
        }
        return render(request, "consultations/answers/no_responses.html", context)

    # Get the question part with themes
    try:
        question_part_with_themes = question.questionpart_set.get(
            type=models.QuestionPart.QuestionType.FREE_TEXT
        )
    except ObjectDoesNotExist:
        return handle_no_responses()

    # Get the next response that has not been checked
    next_response = (
        models.Answer.objects.filter(
            question_part=question_part_with_themes, is_theme_mapping_audited=False
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
