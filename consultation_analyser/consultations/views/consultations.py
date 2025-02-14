import logging
from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    QuestionPart,
    Theme,
    ThemeMapping,
)

from .decorators import user_can_see_consultation

logger = logging.getLogger("upload")


def index(request: HttpRequest) -> HttpResponse:
    user = request.user
    consultations_for_user = Consultation.objects.filter(users=user)
    context = {"consultations": consultations_for_user}
    return render(request, "consultations/consultations/index.html", context)


def get_top_themes_for_free_text_question_part(
    free_text_question_part: QuestionPart, number_top_themes: int = 8
) -> list[dict]:
    # For now, just get latest theme mappings
    theme_mappings_qs = ThemeMapping.get_latest_theme_mappings_for_question_part(
        free_text_question_part
    )
    top_themes_counts_qs = (
        theme_mappings_qs.values("theme")
        .annotate(theme_count=Count("theme"))
        .order_by("-theme_count")
    )[:number_top_themes]
    top_themes_by_counts_list = []
    for item in top_themes_counts_qs:
        theme_obj = Theme.objects.get(id=item["theme"])
        output = {
            "theme": theme_obj,
            "count": item["theme_count"],
        }
        top_themes_by_counts_list.append(output)
    return top_themes_by_counts_list


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    # Dashboard page
    consultation = get_object_or_404(Consultation, slug=consultation_slug)
    questions = Question.objects.filter(consultation__slug=consultation_slug).order_by("number")

    questions_list = []
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
        # For now, assume that we just take the first closed question (in many cases there will be just one)
        # Just take the single option for now
        single_option_question_part = (
            QuestionPart.objects.filter(question=question)
            .filter(type=QuestionPart.QuestionType.SINGLE_OPTION)
            .first()
        )
        if single_option_question_part:
            question_dict["single_option_question_part"] = single_option_question_part
            counts = single_option_question_part.get_option_counts()
            total_responses = single_option_question_part.answer_set.count()
            proportions = OrderedDict((k, v / total_responses) for k, v in counts.items())
            question_dict["single_option_counts"] = counts
            question_dict["single_option_proportions"] = proportions
        questions_list.append(question_dict)
        # Do something similar and just find the first multiple option question part
        multiple_option_question_part = (
            QuestionPart.objects.filter(question=question)
            .filter(type=QuestionPart.QuestionType.MULTIPLE_OPTIONS)
            .first()
        )
        if multiple_option_question_part:
            question_dict["multiple_option_question_part"] = multiple_option_question_part
            counts = multiple_option_question_part.get_option_counts()
            total_responses = multiple_option_question_part.answer_set.count()
            question_dict["multiple_option_counts"] = counts

    context = {
        "all_questions": questions_list,
        "consultation": consultation,
    }
    return render(request, "consultations/consultations/show.html", context)
