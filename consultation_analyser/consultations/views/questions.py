from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, QuerySet
from django.http import HttpRequest
from django.shortcuts import render

from .. import models
from .consultations import NO_THEMES_YET_MESSAGE
from .decorators import user_can_see_consultation
from .filters import get_applied_filters, get_filtered_responses, get_filtered_themes


def get_scatter_plot_data(filtered_themes: QuerySet) -> list[dict]:
    if not filtered_themes:
        return []
    filtered_themes_topic_ids = filtered_themes.values_list("topic_id", flat=True)
    topic_model_metadata = filtered_themes.last().topic_model_metadata
    scatter_plot_data = topic_model_metadata.get_scatter_plot_data_with_detail(
        filtered_themes_topic_ids
    )
    return scatter_plot_data


def get_outliers_info(processing_run: models.ProcessingRun, question: models.Question) -> tuple:
    outlier_theme = None
    outliers_count = 0
    if not processing_run:
        return outlier_theme, outliers_count
    outlier_themes = processing_run.get_themes_for_question(question_id=question.id).filter(
        is_outlier=True
    )
    if outlier_themes:
        outlier_theme = outlier_themes.first()
        outliers_count = models.Answer.objects.filter(themes=outlier_theme).count()
    return outlier_theme, outliers_count


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
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

    scatter_plot_data = get_scatter_plot_data(filtered_themes)

    # Get counts
    total_responses = responses.count()
    multiple_choice_stats = question.multiple_choice_stats()

    highest_theme_count = filtered_themes.aggregate(Max("answer_count"))["answer_count__max"]

    blank_free_text_count = (
        models.Answer.objects.filter(question=question).filter(free_text="").count()
    )

    outlier_theme, outliers_count = get_outliers_info(
        processing_run=processing_run, question=question
    )

    context = {
        "consultation_slug": consultation_slug,
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
        "scatter_plot_data": scatter_plot_data,
    }
    return render(request, "consultations/questions/show.html", context)
