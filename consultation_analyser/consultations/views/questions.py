from django.db.models import Count
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render

from .. import models
from .decorators import user_can_see_consultation


@user_can_see_consultation
def show(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)

    question_parts = models.QuestionPart.objects.filter(question=question).order_by("number")

    # Assume at most one free text part per question.
    free_text_question_part = question_parts.filter(
        type=models.QuestionPart.QuestionType.FREE_TEXT
    ).first()

    # Get counts
    total_responses = models.Answer.objects.filter(question_part=question_parts.first()).count()

    # Get latest themes for the free text part
    theme_counts_dict = {}
    highest_theme_count = 0

    if free_text_question_part:
        latest_theme_mappings = models.ThemeMapping.get_latest_theme_mappings_for_question_part(
            part=free_text_question_part
        )
        theme_counts = (
            latest_theme_mappings.values("theme").annotate(count=Count("theme")).order_by("-count")
        )
        if theme_counts:
            highest_theme_count = theme_counts[0]["count"]
            theme_counts_dict = {
                models.Theme.objects.get(id=theme_count["theme"]): theme_count["count"]
            for theme_count in theme_counts
        }

    context = {
        "consultation_slug": consultation_slug,
        "consultation_name": consultation.title,
        "question": question,
        "question_parts": question_parts,
        "total_responses": total_responses,
        "theme_counts": theme_counts_dict,
        "highest_theme_count": highest_theme_count,
    }
    return render(request, "consultations/questions/show.html", context)


@user_can_see_consultation
def index(request, consultation_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question_parts = models.QuestionPart.objects.filter(
        question__consultation=consultation, type=models.QuestionPart.QuestionType.FREE_TEXT
    )
    context = {
        "consultation": consultation,
        "question_parts": question_parts,
    }
    return render(request, "consultations/questions/index.html", context)
