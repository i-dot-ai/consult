from datetime import datetime
from uuid import UUID

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count, F, Prefetch, Q, QuerySet, Value
from django.db.models.functions import Length, Replace
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .. import models
from .decorators import user_can_see_consultation, user_can_see_dashboards


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
            positive_count=Count("id", filter=Q(stance=models.ThemeMapping.Stance.POSITIVE)),
            negative_count=Count("id", filter=Q(stance=models.ThemeMapping.Stance.NEGATIVE)),
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


@user_can_see_dashboards
@user_can_see_consultation
def respondents_json(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    page_size = request.GET.get("page_size")
    page = request.GET.get(
        "page", 1
    )  # TODO: replace with `last_created_at` when we move to keyset pagination
    # If needed, add request.user.id to make cache unique to each user
    cache_key = f"respondents_{consultation_slug}_{question_slug}"
    cache_timeout = 60 * 20  #  20 mins

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

        filtered_answers = (
            models.Answer.objects.filter(question_part__question__slug=question_slug)
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
            models.Respondent.objects.annotate(num_answers=Count("answer"))
            .filter(
                consultation__slug=consultation_slug,
                num_answers__gt=0,  #  Filter out respondents with no answers
            )
            .order_by("pk")
            .prefetch_related(
                Prefetch("answer_set", queryset=filtered_answers, to_attr="prefetched_answers")
            )
            .distinct()
        )

        # Update cache
        cache.set(cache_key, respondents, timeout=cache_timeout)

    # Pagination
    if page_size:
        pagination = Paginator(respondents, page_size)
        current_page = pagination.page(page)
        respondents = current_page.object_list

    data: dict[str, list] = {"all_respondents": []}

    # Get individual data for each displayed respondent
    for respondent in respondents:
        # Defaults
        free_text_answer = None
        multiple_choice_answers = None

        # Free text response
        free_text_responses = [
            answer
            for answer in respondent.prefetched_answers
            if answer.question_part.type == models.QuestionPart.QuestionType.FREE_TEXT
        ]

        if len(free_text_responses) > 0:
            free_text_answer = free_text_responses[0]

            respondent.themes = free_text_answer.prefetched_thememappings  # type: ignore

            if len(free_text_answer.prefetched_sentimentmappings) > 0:
                respondent.sentiment = free_text_answer.prefetched_sentimentmappings[0]  # type: ignore

            if len(free_text_answer.prefetched_evidencerichmappings) > 0:
                respondent.evidence_rich = free_text_answer.prefetched_evidencerichmappings[0]  # type: ignore

        # Multiple choice response
        multiple_choice_answers = [
            answer
            for answer in respondent.prefetched_answers
            if answer.question_part.type == models.QuestionPart.QuestionType.MULTIPLE_OPTIONS
        ]

        if len(multiple_choice_answers) > 0:
            respondent.multiple_choice_answer = multiple_choice_answers[0]

        # Build JSON response
        data["all_respondents"].append(
            {
                "id": f"response-{getattr(respondent, 'identifier', '')}",
                "identifier": getattr(respondent, "identifier", ""),
                "sentiment_position": respondent.sentiment.position
                if hasattr(respondent, "sentiment") and hasattr(respondent.sentiment, "position")
                else "",
                "free_text_answer_text": free_text_answer.text  # type: ignore
                if hasattr(free_text_answer, "text")
                else "",
                "demographic_data": hasattr(respondent, "data") or "",
                "themes": [
                    {
                        "id": theme.theme.id,
                        "stance": theme.stance,
                        "name": theme.theme.name,
                        "description": theme.theme.description,
                    }
                    for theme in respondent.themes
                ]
                if hasattr(respondent, "themes")
                else [],
                "multiple_choice_answer": [respondent.multiple_choice_answer.chosen_options]
                if hasattr(respondent, "multiple_choice_answer")
                and hasattr(respondent.multiple_choice_answer, "chosen_options")
                else [],
                "evidenceRich": True
                if hasattr(respondent, "evidence_rich") and respondent.evidence_rich.evidence_rich
                else False,
                "individual": True if hasattr(respondent, "individual") else False,
            }
        )

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
    question = models.Question.objects.get(
        slug=question_slug,
        consultation=consultation,
    )
    free_text_question_part = models.QuestionPart.objects.filter(
        question=question, type=models.QuestionPart.QuestionType.FREE_TEXT
    ).first()  # Assume that there is only one free text response
    has_multiple_choice_question_part = models.QuestionPart.objects.filter(
        question=question, type=models.QuestionPart.QuestionType.MULTIPLE_OPTIONS
    ).exists()

    # Get all respondents for question
    respondents = (
        models.Respondent.objects.annotate(num_answers=Count("answer"))
        .filter(
            consultation__slug=consultation_slug,
            num_answers__gt=0,  #  Filter out respondents with no answers
        )
        .distinct()
    )

    has_individual_data = respondents.filter(data__has_key="individual").exists()

    # Get summary data for filtered respondents list
    selected_theme_mappings = get_selected_theme_summary(free_text_question_part, respondents)
    multiple_choice_summary = get_selected_option_summary(question, respondents)

    csv_button_data = [
        {
            "Theme name": mapping.get("theme__name", ""),
            "Total mentions": mapping.get("count", -1),
            "Positive mentions": mapping.get("positive_count", -1),
            "Negative mentions": mapping.get("negative_count", -1),
        }
        for mapping in selected_theme_mappings
    ]

    context = {
        "consultation_name": consultation.title,
        "consultation_slug": consultation_slug,
        "question": question,
        "question_slug": question_slug,
        "free_text_question_part": free_text_question_part,
        "has_multiple_choice_question_part": has_multiple_choice_question_part,
        "selected_theme_mappings": selected_theme_mappings,
        "csv_button_data": csv_button_data,
        "multiple_choice_summary": multiple_choice_summary,
        "stance_options": models.SentimentMapping.Position.names,
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
