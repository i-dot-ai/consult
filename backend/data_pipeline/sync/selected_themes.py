import csv
import io

from django.conf import settings

from consultations.constants import NO_REASON_GIVEN_THEME_NAME, OTHER_THEME_NAME
from consultations.models import (
    Consultation,
    SelectedTheme,
)
from consultations.utils.s3 import get_s3_client

logger = settings.LOGGER


def export_selected_themes_to_s3(consultation: Consultation) -> int:
    """
    Export all selected themes for a consultation to S3.

    This prepares for the 'assign-themes' batch job, which expects themes in
    the format: app_data/consultations/{code}/inputs/question_part_{N}/themes.csv

    Args:
        consultation: The consultation whose themes should be exported

    Returns:
        Number of questions that had themes exported

    Raises:
        ValueError: If no questions have selected themes
    """

    questions = list(consultation.question_set.filter(has_free_text=True))

    themes_by_question: dict = {}
    for theme in SelectedTheme.objects.filter(question__in=questions):
        themes_by_question.setdefault(theme.question_id, []).append(theme)

    generic_theme_names = {OTHER_THEME_NAME.lower(), NO_REASON_GIVEN_THEME_NAME.lower()}
    missing = [
        q.number
        for q in questions
        if not any(
            theme.name.lower() not in generic_theme_names
            for theme in themes_by_question.get(q.id, [])
        )
    ]
    if missing:
        raise ValueError(
            f"Questions {missing} have no selected themes for consultation '{consultation.title}'"
        )

    s3_client = get_s3_client()
    questions_exported = 0

    for question in questions:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Theme Name", "Theme Description"])

        themes = themes_by_question.get(question.id, [])

        for theme in themes:
            writer.writerow([theme.name, theme.description])

        s3_path = (
            f"app_data/consultations/{consultation.code}/inputs/"
            f"question_part_{question.number}/themes.csv"
        )
        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME, Key=s3_path, Body=csv_buffer.getvalue()
        )

        logger.info(
            "Exported {themes_count} themes for question {question_number} to {s3_path}",
            themes_count=len(themes),
            question_number=question.number,
            s3_path=s3_path,
        )
        questions_exported += 1

    logger.info(
        f"Exported themes for {questions_exported} questions in consultation '{consultation.title}'"
    )

    return questions_exported
