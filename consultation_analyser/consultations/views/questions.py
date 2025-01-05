from typing import Dict, List, Tuple

from django.contrib.auth.decorators import login_required
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render

from .. import models
from .decorators import user_can_see_consultation

# from .filters import filter_answers_by_keyword, get_applied_filters, get_filtered_answers, get_filtered_themes


def filter_scatter_plot_data(filtered_themes: QuerySet) -> List[Dict]:
    if not filtered_themes:
        return []
    theme = filtered_themes.first()  # metadata same for all themes for question
    topic_model_metadata = theme.topic_model_metadata
    data = topic_model_metadata.scatter_plot_data
    if not data:  # Old consultations - didn't calculate scatter data when generating themes
        return []
    data = data["data"]
    topic_ids = [theme.topic_id for theme in filtered_themes]
    filtered_scatter_data = [
        coordinate for coordinate in data if coordinate["topic_id"] in topic_ids
    ]
    return filtered_scatter_data


def get_outliers_info(processing_run: models.ProcessingRun, question: models.QuestionOld) -> Tuple:
    outlier_theme = None
    outliers_count = 0
    if not processing_run:
        return outlier_theme, outliers_count
    outlier_themes = processing_run.get_themes_for_question(question_id=question.id).filter(
        is_outlier=True
    )
    if outlier_themes:
        outlier_theme = outlier_themes.first()
        outliers_count = models.AnswerOld.objects.filter(themes=outlier_theme).count()
    return outlier_theme, outliers_count


@user_can_see_consultation
def show(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    consultation = get_object_or_404(models.Consultation2, slug=consultation_slug)
    question = get_object_or_404(models.Question2, slug=question_slug, consultation=consultation)

    question_parts = models.QuestionPart.objects.filter(question=question).order_by("order")

    # Assume at most one free text part per question.
    free_text_question_part = question_parts.filter(
        type=models.QuestionPart.QuestionType.FREE_TEXT
    ).first()
    # closed_question_parts = question_parts.filter(type__in=[models.QuestionPart.QuestionType.SINGLE_OPTION, models.QuestionPart.QuestionType.MULTIPLE_OPTIONS]).order_by("order")

    # Get counts
    total_responses = models.Answer2.objects.filter(question_part=question_parts.first()).count()

    # Get latest themes for the free text part
    # TODO - order by count?
    if free_text_question_part:
        latest_theme_mappings = models.ThemeMapping.get_latest_theme_mappings_for_question_part(
            part=free_text_question_part
        )
        theme_counts = (
            latest_theme_mappings.values("theme").annotate(count=Count("theme")).order_by("-count")
        )
        highest_theme_count = theme_counts[0]["count"]
        theme_counts_dict = {
            models.Theme2.objects.get(id=theme_count["theme"]): theme_count["count"]
            for theme_count in theme_counts
        }
        print(theme_counts_dict)
    else:
        theme_counts_dict = {}
        highest_theme_count = 0

    context = {
        "consultation_slug": consultation_slug,
        "consultation_name": consultation.text,
        "question": question,
        "question_parts": question_parts,
        "total_responses": total_responses,
        "theme_counts": theme_counts_dict,
        "highest_theme_count": highest_theme_count,
    }
    return render(request, "consultations/questions/show.html", context)
