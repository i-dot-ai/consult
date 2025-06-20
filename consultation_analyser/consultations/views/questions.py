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

    # Get counts
    total_responses = models.Response.objects.filter(question=question).count()

    # Get latest themes for the free text part
    theme_counts_dict = {}
    highest_theme_count = 0

    if question.has_free_text:
        theme_counts = (
            models.Theme.objects.filter(question=question, responseannotation__isnull=False)
            .annotate(count=Count("responseannotation"))
            .order_by("-count")
        )
        if theme_counts:
            highest_theme_count = theme_counts[0].count
            theme_counts_dict = {theme: theme.count for theme in theme_counts}

    context = {
        "consultation_slug": consultation_slug,
        "consultation_name": consultation.title,
        "question": question,
        "question_parts": [question],  # For template compatibility
        "total_responses": total_responses,
        "theme_counts": theme_counts_dict,
        "highest_theme_count": highest_theme_count,
    }
    return render(request, "consultations/questions/show.html", context)


@user_can_see_consultation
def index(request, consultation_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)

    # Get questions that have free text and have themes
    questions_with_themes = models.Question.objects.filter(
        consultation=consultation, has_free_text=True, theme__isnull=False
    ).distinct()

    context = {
        "consultation": consultation,
        "question_parts": questions_with_themes,  # Using same variable name for template compatibility
    }
    return render(request, "consultations/questions/index.html", context)
