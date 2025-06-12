import json
import logging

from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from consultation_analyser.consultations.models import (
    ConsultationOld,
    QuestionOld,
    QuestionPart,
    SentimentMapping,
    ThemeMapping,
    ThemeOld,
)

from .decorators import user_can_see_consultation, user_can_see_dashboards

logger = logging.getLogger("upload")


def index(request: HttpRequest) -> HttpResponse:
    user = request.user
    consultations_for_user = ConsultationOld.objects.filter(users=user)
    context = {
        "consultations": consultations_for_user,
        "user_has_dashboard_access": user.has_dashboard_access,
    }
    return render(request, "consultations/consultations/index.html", context)


def get_counts_of_sentiment(free_text_question_part: QuestionPart) -> dict:
    """Gives agree/disagree/unclear/no position counts for responses to the free text question."""
    total_answers = free_text_question_part.answer_set.all().count()
    sentiments_for_question_part_qs = SentimentMapping.objects.filter(
        answer__question_part=free_text_question_part
    )
    number_in_agreement = sentiments_for_question_part_qs.filter(
        position=SentimentMapping.Position.AGREEMENT
    ).count()
    number_in_disagreement = sentiments_for_question_part_qs.filter(
        position=SentimentMapping.Position.DISAGREEMENT
    ).count()
    number_unclear = sentiments_for_question_part_qs.filter(
        position=SentimentMapping.Position.UNCLEAR
    ).count()
    # Any answers not assigned a position
    number_no_position = (
        total_answers - number_in_agreement - number_in_disagreement - number_unclear
    )
    sentiment_counts = {
        "agreement": number_in_agreement,
        "disagreement": number_in_disagreement,
        "unclear": number_unclear,
        "no_position": number_no_position,
    }
    return sentiment_counts


def get_top_themes_for_free_text_question_part(
    free_text_question_part: QuestionPart, number_top_themes: int = 8
) -> list[dict]:
    # For now, just get latest theme mappings
    theme_mappings_qs = ThemeMapping.get_latest_theme_mappings(free_text_question_part)
    top_themes_counts_qs = (
        theme_mappings_qs.values("theme")
        .annotate(theme_count=Count("theme"))
        .order_by("-theme_count")
    )[:number_top_themes]
    top_themes_counts_qs = (
        theme_mappings_qs.values("theme")
        .annotate(theme_count=Count("theme"))
        .order_by("-theme_count")
    )
    top_themes_by_counts_list = []
    for item in top_themes_counts_qs:
        theme_obj = ThemeOld.objects.get(id=item["theme"])
        output = {
            "theme": theme_obj,
            "count": item["theme_count"],
        }
        top_themes_by_counts_list.append(output)
    return top_themes_by_counts_list


@user_can_see_dashboards
@user_can_see_consultation
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    # Dashboard page
    consultation = get_object_or_404(ConsultationOld, slug=consultation_slug)
    questions = QuestionOld.objects.filter(consultation__slug=consultation_slug).order_by("number")

    all_questions = []
    for question in questions:
        question_dict = {"question": question}
        # Get free text question stuff
        free_text_question_part = (
            QuestionPart.objects.filter(question=question)
            .filter(type=QuestionPart.QuestionType.FREE_TEXT)
            .first()
        )
        if free_text_question_part:
            question_dict["free_text_question_part"] = free_text_question_part
            top_themes_by_counts_list = get_top_themes_for_free_text_question_part(
                free_text_question_part
            )
            question_dict["theme_counts"] = top_themes_by_counts_list
            question_dict["sentiment_counts"] = get_counts_of_sentiment(free_text_question_part)
        # For now, assume that we just take the first closed question (in many cases there will be just one)
        # Just take the single option for now
        single_option_question_part = (
            QuestionPart.objects.filter(question=question)
            .filter(type=QuestionPart.QuestionType.SINGLE_OPTION)
            .first()
        )
        if single_option_question_part:
            question_dict["single_option_question_part"] = single_option_question_part
            question_dict["single_option_counts"] = json.dumps(
                single_option_question_part.get_option_counts()
            )

        # Do something similar and just find the first multiple option question part
        multiple_option_question_part = (
            QuestionPart.objects.filter(question=question)
            .filter(type=QuestionPart.QuestionType.MULTIPLE_OPTIONS)
            .first()
        )
        if multiple_option_question_part:
            question_dict["multiple_option_question_part"] = multiple_option_question_part
            question_dict["multiple_option_counts"] = json.dumps(
                multiple_option_question_part.get_option_counts()
            )

        all_questions.append(question_dict)

    # What is the right number per page?
    pagination = Paginator(all_questions, 2)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_questions = current_page.object_list

    context = {
        "consultation": consultation,
        "pagination": current_page,
        "questions_list": paginated_questions,
        "all_questions_list": all_questions,
    }
    return render(request, "consultations/consultations/show.html", context)
