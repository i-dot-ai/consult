from collections import defaultdict
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count, F, Prefetch, Q, QuerySet, Subquery, Value
from django.db.models.functions import Length, Replace
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .. import models
from .decorators import user_can_see_consultation, user_can_see_dashboards


class DataDict(TypedDict):
    all_respondents: list
    has_more_pages: bool


def filter_by_response_and_theme(
    question: models.Question,
    respondents: QuerySet,
    responseid: str | None = None,
    responsesentiment: list[str] | None = None,
    themesfilter: list[str] | None = None,
    themesentiment: list[str] | None = None,
) -> QuerySet:
    """filter respondents by response themes"""
    if responseid:
        respondents = respondents.filter(
            themefinder_respondent_id=responseid,
            answer__question_part__question=question,
        )
    if responsesentiment:
        respondents = respondents.filter(
            answer__in=models.Answer.objects.filter(
                sentimentmapping__position=responsesentiment, question_part__question=question
            )
        )
    if themesfilter:
        respondents = respondents.filter(answer__thememapping__theme__in=themesfilter)
    if themesentiment:
        respondents = respondents.filter(answer__thememapping__stance=themesentiment)

    return respondents.distinct()


def filter_by_word_count(
    respondents: QuerySet,
    question_slug: str,
    word_count: int,
) -> QuerySet:
    """filter respondents by word count"""
    respondents = respondents.annotate(
        # Calculates the difference between the length of the text and the length of the text with spaces removed and add 1
        word_count=Length("answer__text")
        - Length(Replace(F("answer__text"), Value(" "), Value("")))
        + 1
    )

    annotated_responses = (
        models.Answer.objects.filter(
            question_part__question__slug=question_slug,
        )
        .annotate(word_count=Length("text") - Length(Replace(F("text"), Value(" "), Value(""))) + 1)
        .filter(word_count__gte=word_count)
    )

    return respondents.filter(answer__in=annotated_responses)


def filter_by_demographic_data(
    respondents: QuerySet,
    demographicindividual: list[str] | None = None,
) -> QuerySet:
    """filter respondents by demographic data"""

    has_individual_data = respondents.filter(data__has_key="individual").exists()

    if not demographicindividual:
        return has_individual_data, respondents

    filtered_respondents = respondents.filter(data__individual__in=demographicindividual)

    return has_individual_data, filtered_respondents


def get_selected_theme_summary(
    free_text_question_part: models.QuestionPart, respondents: QuerySet
) -> tuple[QuerySet, dict]:
    """Get a summary of the selected themes for a free text question"""
    # Assume latest framework for now
    theme_mappings_qs = models.ThemeMapping.get_latest_theme_mappings(
        question_part=free_text_question_part
    )
    selected_theme_mappings = (
        theme_mappings_qs.filter(answer__respondent__in=respondents)
        .values("theme__name", "theme__description", "theme__id")
        .annotate(
            count=Count("id"),
        )
    )
    return selected_theme_mappings


def get_selected_option_summary(question: models.Question, respondents: QuerySet) -> list[dict]:
    """Get a summary of the selected options for a multiple choice question"""
    annotated_responses = [
        models.Answer.objects.filter(question_part=question_part, respondent__in=respondents)
        .distinct()
        .values("chosen_options")
        .order_by("chosen_options")
        .annotate(count=Count("id"))
        for question_part in question.questionpart_set.filter(
            type=models.QuestionPart.QuestionType.MULTIPLE_OPTIONS
        )
    ]

    multichoice_summary = []
    for responses in annotated_responses:
        option_counts = {}
        for response in responses:
            for option in response["chosen_options"]:
                if option not in option_counts:
                    option_counts[option] = 0
                option_counts[option] += response["count"]
        multichoice_summary.append(option_counts)

    return multichoice_summary


def get_respondents_for_question(
    consultation_slug: str, question_slug: str, cache_timeout: int = 60 * 20
) -> QuerySet[models.Respondent]:
    # Cache data for question/consultation. Default timeout to 20 mins.
    cache_key = f"respondents_{consultation_slug}_{question_slug}"

    # Retrieve cached data
    respondents = cache.get(cache_key)

    # If no cached data found
    if respondents is None:
        # Prefetch all related data to avoid multiple db hits
        # filtered_answers is not querying the database yet,
        # only building the query (as querysets are lazily fetched).
        # This then gets passed as the queryset param of respondent prefetch,
        # updating that query with the filter logic.
        # Ultimately the returned answers are only for the current consultation.
        answers = (
            models.Answer.objects.filter(
                question_part__question__slug=question_slug,
                question_part__question__consultation__slug=consultation_slug,
            )
            .select_related("respondent")
            .prefetch_related(
                Prefetch(
                    "thememapping_set",
                    queryset=models.ThemeMapping.objects.select_related("theme"),
                    to_attr="prefetched_thememappings",
                )
            )
            .prefetch_related(
                Prefetch("evidencerichmapping_set", to_attr="prefetched_evidencerichmappings")
            )
            .prefetch_related(
                Prefetch("sentimentmapping_set", to_attr="prefetched_sentimentmappings")
            )
        )

        respondents = (
            models.Respondent.objects.filter(
                id__in=Subquery(answers.values_list("respondent_id", flat=True))
            )
            .prefetch_related(
                Prefetch(
                    "answer_set", queryset=answers, to_attr="prefetched_answers"
                )  # Prefetch the necessary answers
            )
            .order_by("pk")
        )

        # Update cache
        cache.set(cache_key, respondents, timeout=cache_timeout)
    return respondents


@user_can_see_dashboards
@user_can_see_consultation
def respondents_json(request: HttpRequest, consultation_slug: str, question_slug: str):
    page_size = request.GET.get("page_size")
    page = request.GET.get("page", 1)

    # NEW: pull Response rows directly (denormalised)
    respondents = (
        models.Response.objects.select_related("respondent")
        .filter(consultation__slug=consultation_slug, question__slug=question_slug)
        .order_by("id")  # keep deterministic order for pagination
    )
    query = Q()

    sentiment_list = request.GET.get("sentimentFilters", "").split(",")
    sentiment_list = [s for s in sentiment_list if s]
    if sentiment_list:
        query &= Q(sentiment__in=sentiment_list)

    theme_list = request.GET.get("themeFilters", "").split(",")
    theme_list = [t for t in theme_list if t]
    if theme_list:
        theme_q = Q()
        for t in theme_list:
            # simple text match inside JSON array
            theme_q |= Q(themes__icontains=f'"theme_key":"{t}"')
        query &= theme_q

    if request.GET.get("evidenceRichFilter") == "evidence-rich":
        query &= Q(evidence_rich=models.Response.EvidenceRich.YES)

    respondents = respondents.filter(query)

    data: dict[str, object] = {"all_respondents": [], "has_more_pages": False}

    # Pagination (unchanged)
    if page_size:
        pagination = Paginator(respondents, page_size)
        current_page = pagination.page(page)
        respondents = current_page.object_list
        data["has_more_pages"] = current_page.has_next()

    # Build payload
    for resp in respondents:  # resp == Response instance
        respondent = resp.respondent  # convenience
        themes_payload = [
            {
                "id": t.get("theme_key"),  # was theme.theme.id
                "name": t.get("theme_name"),
                "description": t.get("theme_description"),
            }
            for t in (resp.themes or [])
        ]

        data["all_respondents"].append(
            {
                "id": f"response-{resp.id}",
                "identifier": respondent.identifier,
                "sentiment_position": resp.sentiment or "",
                "free_text_answer_text": resp.free_text_answer or "",
                "demographic_data": bool(respondent.data),
                "themes": themes_payload,  # already denormalised JSON
                "multiple_choice_answer": [],  # not present in new model
                "evidenceRich": resp.evidence_rich == models.Response.EvidenceRich.YES,
                "individual": False,  # adjust if you store flag elsewhere
            }
        )

    # TODO: add filtering to this endpoint. see Nina's PR

    return JsonResponse(data)


# THIS IS what we need to update for themes table, need to include filtering here. think of a better name!
@user_can_see_dashboards
@user_can_see_consultation
def index(request: HttpRequest, consultation_slug: str, question_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = models.Question.objects.get(slug=question_slug, consultation=consultation)

    responses_qs = models.Response.objects.select_related("respondent").filter(question=question)
    query = Q()

    sentiment_list = request.GET.get("sentimentFilters", "").split(",")
    sentiment_list = [s for s in sentiment_list if s]
    if sentiment_list:
        query &= Q(sentiment__in=sentiment_list)

    theme_list = request.GET.get("themeFilters", "").split(",")
    theme_list = [t for t in theme_list if t]
    if theme_list:
        theme_q = Q()
        for t in theme_list:
            theme_q |= Q(themes__icontains=f'"theme_key":"{t}"')
        query &= theme_q

    if request.GET.get("evidenceRichFilter") == "evidence-rich":
        query &= Q(evidence_rich=models.Response.EvidenceRich.YES)

    responses_qs = responses_qs.filter(query)

    has_individual_data = responses_qs.filter(respondent__data__has_key="individual").exists()
    theme_counter: defaultdict[tuple[str, str, str], int] = defaultdict(int)

    for resp in responses_qs:
        for theme in resp.themes or []:
            key = (
                theme.get("theme_key", ""),
                theme.get("theme_name", ""),
                theme.get("theme_description", ""),
            )
            theme_counter[key] += 1

    selected_theme_mappings = [
        {
            "theme__key": k,
            "theme__name": n,
            "theme__description": d,
            "count": c,
        }
        for (k, n, d), c in theme_counter.items()
    ]
    selected_theme_mappings.sort(key=lambda m: m["count"], reverse=True)

    has_multiple_choice_question_part = False
    multiple_choice_summary = []

    csv_button_data = [
        {"Theme name": m["theme__name"], "Total mentions": m["count"]}
        for m in selected_theme_mappings
    ]

    context = {
        "consultation_name": consultation.title,
        "consultation_slug": consultation_slug,
        "question": question,
        "question_slug": question_slug,
        "free_text_question_part": None,  # no longer used
        "has_multiple_choice_question_part": has_multiple_choice_question_part,
        "selected_theme_mappings": selected_theme_mappings,
        "csv_button_data": csv_button_data,
        "multiple_choice_summary": multiple_choice_summary,
        "stance_options": models.Response.SentimentPosition.names,
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
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)
    response = get_object_or_404(models.Answer, id=response_id)
    question_part = response.question_part

    all_theme_mappings_for_framework = models.ThemeMapping.get_latest_theme_mappings(question_part)

    latest_framework = (
        models.Framework.objects.filter(question_part=question_part).order_by("created_at").last()
    )
    all_themes = models.Theme.objects.filter(
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
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)

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
