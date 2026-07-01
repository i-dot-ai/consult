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

    questions = consultation.question_set.filter(has_free_text=True)

    non_generic_themes_by_question = {
        question: SelectedTheme.objects.filter(question=question)
        .exclude(name__iexact=OTHER_THEME_NAME)
        .exclude(name__iexact=NO_REASON_GIVEN_THEME_NAME)
        for question in questions
    }

    missing = [
        q.number for q, themes in non_generic_themes_by_question.items() if not themes.exists()
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

        themes = SelectedTheme.objects.filter(question=question)

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
            themes_count=themes.count(),
            question_number=question.number,
            s3_path=s3_path,
        )
        questions_exported += 1

    logger.info(
        f"Exported themes for {questions_exported} questions in consultation '{consultation.title}'"
    )

    return questions_exported
