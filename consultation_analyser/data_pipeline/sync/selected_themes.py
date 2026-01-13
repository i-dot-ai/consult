import csv
import io

import boto3
from django.conf import settings

from consultation_analyser.consultations.models import (
    Consultation,
    SelectedTheme,
)

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

    s3_client = boto3.client("s3")
    questions_exported = 0

    questions = consultation.question_set.filter(has_free_text=True)

    for question in questions:
        themes = SelectedTheme.objects.filter(question=question)

        if not themes.exists():
            logger.warning(
                f"No selected themes found for question {question.number} "
                f"in consultation {consultation.title}"
            )
            continue

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Theme Name", "Theme Description"])

        for theme in themes:
            writer.writerow([theme.name, theme.description])

        s3_path = (
            f"app_data/consultations/{consultation.code}/inputs/"
            f"question_part_{question.number}/themes.csv"
        )
        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME, Key=s3_path, Body=csv_buffer.getvalue()
        )

        logger.info(f"Exported {themes.count()} themes for question {question.number} to {s3_path}")
        questions_exported += 1

    if questions_exported == 0:
        raise ValueError(
            f"No questions with selected themes found for consultation '{consultation.title}'"
        )

    logger.info(
        f"Exported themes for {questions_exported} questions in consultation '{consultation.title}'"
    )

    return questions_exported
