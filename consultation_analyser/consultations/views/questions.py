from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render

from .. import models
from .consultations import NO_THEMES_YET_MESSAGE
from .decorators import user_can_see_consultation
from .filters import get_applied_filters, get_filtered_responses, get_filtered_themes


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = models.Question.objects.get(
        slug=question_slug,
        section__slug=section_slug,
        section__consultation__slug=consultation_slug,
    )

    consultation = question.section.consultation
    if not consultation.has_processing_run():
        messages.info(request, NO_THEMES_YET_MESSAGE)

    # TODO - for now default to latest processing run
    processing_run = consultation.latest_processing_run

    applied_filters = get_applied_filters(request)
    responses = get_filtered_responses(question, applied_filters)
    filtered_themes = (
        get_filtered_themes(question, applied_filters, processing_run=processing_run)
        .annotate(answer_count=Count("answer"))
        .order_by("-answer_count")
    )  # Gets latest themes only

    # Get counts
    total_responses = responses.count()
    multiple_choice_stats = question.multiple_choice_stats()

    highest_theme_count = filtered_themes.aggregate(Max("answer_count"))["answer_count__max"]

    blank_free_text_count = (
        models.Answer.objects.filter(question=question).filter(free_text="").count()
    )

    outlier_theme = None
    outliers_count = 0
    if processing_run:
        outlier_themes = processing_run.get_themes_for_question(question_id=question.id).filter(
            is_outlier=True
        )
        if outlier_themes:
            outlier_theme = outlier_themes.first()
            outliers_count = models.Answer.objects.filter(themes=outlier_theme).count()

    context = {
        "consultation_slug": consultation_slug,
        "consultation_name": consultation.name,
        "question": question,
        "multiple_choice_stats": multiple_choice_stats,
        "responses": responses,
        "themes": filtered_themes,
        "highest_theme_count": highest_theme_count,
        "total_responses": total_responses,
        "applied_filters": applied_filters,
        "blank_free_text_count": blank_free_text_count,
        "outliers_count": outliers_count,
        "outlier_theme_id": outlier_theme.id if outlier_theme else None,
    }
    return render(request, "consultations/questions/show.html", context)
