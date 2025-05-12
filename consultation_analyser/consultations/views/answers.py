from datetime import datetime
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, QuerySet, Sum, Value
from django.db.models.functions import Length, Replace
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.core.cache import cache
from django.http import JsonResponse
from django.core import serializers

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

    theme_mapping_summary = selected_theme_mappings.aggregate(
        total=Sum("count"),
        positive=Sum("positive_count"),
        negative=Sum("negative_count"),
    )

    return selected_theme_mappings, theme_mapping_summary


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
    cache_key = f"respondents_{request.user.id}"
    cache_timeout = 60 * 20 #  20 mins

    respondents_cache_key = f"respondents_{request.user.id}"

    responseid = request.GET.get("responseid")
    demographicindividual = request.GET.getlist("demographicindividual")
    themesfilter = request.GET.getlist("themesfilter")
    themesentiment = request.GET.get("themesentiment")
    responsesentiment = request.GET.get("responsesentiment")
    wordcount = request.GET.get("wordcount")
    active_filters = {
        "responseid": {
            "label": "Respondent ID",
            "selected": [{"display": responseid, "id": responseid}] if responseid else [],
        },
        "demographicindividual": {
            "label": "Individual or Organisation",
            "selected": [{"display": d, "id": d} for d in demographicindividual],
        },
        "themesfilter": {
            "label": "Theme",
            "selected": [
                {"display": models.Theme.objects.get(id=t).name, "id": t} for t in themesfilter
            ],
        },
        "themesentiment": {
            "label": "Theme sentiment",
            "selected": [{"display": themesentiment.title(), "id": themesentiment}]
            if themesentiment
            else [],
        },
        "responsesentiment": {
            "label": "Response sentiment",
            "selected": [{"display": responsesentiment.title(), "id": responsesentiment}]
            if responsesentiment
            else [],
        },
        "wordcount": {
            "label": "Minimum word count",
            "selected": [{"display": wordcount, "id": wordcount}] if wordcount else [],
        },
    }
    
    respondents = cache.get(respondents_cache_key)

    if respondents is None:
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
        theme_mappings = (
            models.ThemeMapping.get_latest_theme_mappings(question_part=free_text_question_part)
            .values("theme__name", "theme__description", "theme__id")
            .order_by("theme__name")
            .distinct("theme__name")
        )
        
        # Get respondents list, applying relevant filters
        respondents = filter_by_response_and_theme(
            question,
            models.Respondent.objects.filter(consultation=consultation),
            responseid,
            responsesentiment,
            themesfilter,
            themesentiment,
        ).distinct()

        if wordcount:
            respondents = filter_by_word_count(respondents, question_slug, int(wordcount))

        has_individual_data, respondents = filter_by_demographic_data(
            respondents, demographicindividual
        )

        # Get summary data for filtered respondents list
        selected_theme_mappings, theme_mapping_summary = get_selected_theme_summary(
            free_text_question_part, respondents
        )
        multiple_choice_summary = get_selected_option_summary(question, respondents)

        # Get individual data for each displayed respondent
        for respondent in respondents:
            # Free text response
            try:
                respondent.free_text_answer = models.Answer.objects.get(
                    question_part__question=question,
                    question_part__type=models.QuestionPart.QuestionType.FREE_TEXT,
                    respondent=respondent,
                )
                respondent.sentiment = models.SentimentMapping.objects.filter(
                    answer=respondent.free_text_answer,
                ).last()
                respondent.themes = models.ThemeMapping.objects.filter(
                    answer=respondent.free_text_answer
                )
                respondent.evidence_rich = models.EvidenceRichMapping.objects.filter(
                    answer=respondent.free_text_answer
                ).last()
            except models.Answer.DoesNotExist:
                pass

            # Multiple choice response
            try:
                respondent.multiple_choice_answer = models.Answer.objects.get(
                    question_part__question=question,
                    question_part__type=models.QuestionPart.QuestionType.MULTIPLE_OPTIONS,
                    respondent=respondent,
                )
            except models.Answer.DoesNotExist:
                pass

        display_respondent_id_filter = respondents.filter(
            themefinder_respondent_id__isnull=False
        ).exists()
        
        csv_button_data = [{
            "Theme name": mapping.get("theme__name", ""),
            "Total mentions": mapping.get('count', -1),
            "Positive mentions": mapping.get("positive_count", -1),
            "Negative mentions": mapping.get("negative_count", -1),
        } for mapping in selected_theme_mappings]
    
        cache.set(respondents_cache_key, list(respondents), timeout=cache_timeout)

    return JsonResponse({
        "all_respondents": serializers.serialize("json", respondents, fields=["identifier"])
    })

@user_can_see_dashboards
@user_can_see_consultation
def index(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    responseid = request.GET.get("responseid")
    demographicindividual = request.GET.getlist("demographicindividual")
    themesfilter = request.GET.getlist("themesfilter")
    themesentiment = request.GET.get("themesentiment")
    responsesentiment = request.GET.get("responsesentiment")
    wordcount = request.GET.get("wordcount")
    active_filters = {
        "responseid": {
            "label": "Respondent ID",
            "selected": [{"display": responseid, "id": responseid}] if responseid else [],
        },
        "demographicindividual": {
            "label": "Individual or Organisation",
            "selected": [{"display": d, "id": d} for d in demographicindividual],
        },
        "themesfilter": {
            "label": "Theme",
            "selected": [
                {"display": models.Theme.objects.get(id=t).name, "id": t} for t in themesfilter
            ],
        },
        "themesentiment": {
            "label": "Theme sentiment",
            "selected": [{"display": themesentiment.title(), "id": themesentiment}]
            if themesentiment
            else [],
        },
        "responsesentiment": {
            "label": "Response sentiment",
            "selected": [{"display": responsesentiment.title(), "id": responsesentiment}]
            if responsesentiment
            else [],
        },
        "wordcount": {
            "label": "Minimum word count",
            "selected": [{"display": wordcount, "id": wordcount}] if wordcount else [],
        },
    }

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
    theme_mappings = (
        models.ThemeMapping.get_latest_theme_mappings(question_part=free_text_question_part)
        .values("theme__name", "theme__description", "theme__id")
        .order_by("theme__name")
        .distinct("theme__name")
    )

    # Get respondents list, applying relevant filters
    respondents = filter_by_response_and_theme(
        question,
        models.Respondent.objects.filter(consultation=consultation),
        responseid,
        responsesentiment,
        themesfilter,
        themesentiment,
    ).distinct()

    if wordcount:
        respondents = filter_by_word_count(respondents, question_slug, int(wordcount))

    has_individual_data, respondents = filter_by_demographic_data(
        respondents, demographicindividual
    )

    # Get summary data for filtered respondents list
    selected_theme_mappings, theme_mapping_summary = get_selected_theme_summary(
        free_text_question_part, respondents
    )
    multiple_choice_summary = get_selected_option_summary(question, respondents)

    # Pagination
    pagination = Paginator(respondents, 5)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_respondents = current_page.object_list

    # Get individual data for each displayed respondent
    for respondent in paginated_respondents:
        # Free text response
        try:
            respondent.free_text_answer = models.Answer.objects.get(
                question_part__question=question,
                question_part__type=models.QuestionPart.QuestionType.FREE_TEXT,
                respondent=respondent,
            )
            respondent.sentiment = models.SentimentMapping.objects.filter(
                answer=respondent.free_text_answer,
            ).last()
            respondent.themes = models.ThemeMapping.objects.filter(
                answer=respondent.free_text_answer
            )
            respondent.evidence_rich = models.EvidenceRichMapping.objects.filter(
                answer=respondent.free_text_answer
            ).last()
        except models.Answer.DoesNotExist:
            pass

        # Multiple choice response
        try:
            respondent.multiple_choice_answer = models.Answer.objects.get(
                question_part__question=question,
                question_part__type=models.QuestionPart.QuestionType.MULTIPLE_OPTIONS,
                respondent=respondent,
            )
        except models.Answer.DoesNotExist:
            pass

    csv_button_data = [{
        "Theme name": mapping.get("theme__name", ""),
        "Total mentions": mapping.get('count', -1),
        "Positive mentions": mapping.get("positive_count", -1),
        "Negative mentions": mapping.get("negative_count", -1),
    } for mapping in selected_theme_mappings]

    context = {
        "consultation_name": consultation.title,
        "consultation_slug": consultation_slug,
        "question": question,
        "free_text_question_part": free_text_question_part,
        "has_multiple_choice_question_part": has_multiple_choice_question_part,
        "theme_mappings": theme_mappings,
        "total_responses": len(respondents),
        "pagination": current_page,
        "respondents": paginated_respondents,
        "selected_theme_mappings": selected_theme_mappings,
        "csv_button_data": csv_button_data,
        "theme_mapping_summary": theme_mapping_summary,
        "multiple_choice_summary": multiple_choice_summary,
        "stance_options": models.SentimentMapping.Position.names,
        "theme_stance_options": models.ThemeMapping.Stance.names,
        "active_filters": active_filters,
        "has_filters": any(
            [active_filter["selected"] for active_filter in active_filters.values()]
        ),
        "has_individual_data": has_individual_data,
        "display_respondent_id_filter": respondents.filter(
            themefinder_respondent_id__isnull=False
        ).exists(),
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
