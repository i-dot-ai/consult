from uuid import UUID

from django.conf import settings
from django.db import connection
from django_rq import job

from consultation_analyser.consultations import models

logger = settings.LOGGER


def delete_question_related_table(table: str, consultation_id: UUID):
    logger.info("Deleting records from table={table}", table=table)

    with connection.cursor() as cursor:
        sql = f"""
        DELETE FROM {table}
        WHERE question_id IN (
            SELECT id FROM consultations_question
            WHERE consultation_id = %s
        )"""  # nosec B608
        cursor.execute(sql, [consultation_id])


def delete_response_related_table(table: str, consultation_id: UUID):
    logger.info("Deleting records from table={table}", table=table)

    with connection.cursor() as cursor:
        sql = f"""
        DELETE FROM {table}
        WHERE response_id IN (
            SELECT r.id from consultations_response r
            JOIN consultations_question q ON r.question_id = q.id
            WHERE q.consultation_id = %s
        )"""  # nosec B608
        cursor.execute(sql, [consultation_id])


def delete_consultation_related_table(table: str, consultation_id: UUID):
    """Delete records from a table that directly references consultation_id"""
    logger.info("Deleting records from table={table}", table=table)

    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM {table} WHERE consultation_id = %s",  # nosec B608
            [consultation_id],
        )


def delete_respondent_related_table(table: str, consultation_id: UUID):
    """Delete records from a table that references respondent_id"""
    logger.info("Deleting records from table={table}", table=table)

    with connection.cursor() as cursor:
        sql = f"""
        DELETE FROM {table}
        WHERE respondent_id IN (
            SELECT id FROM consultations_respondent
            WHERE consultation_id = %s
        )"""  # nosec B608
        cursor.execute(sql, [consultation_id])


def delete_response_annotation_themes(consultation_id: UUID):
    """Delete response annotation themes for a consultation"""
    with connection.cursor() as cursor:
        cursor.execute(  # nosec B608
            """
        DELETE FROM consultations_responseannotationtheme
        WHERE response_annotation_id IN (
            SELECT a.id from consultations_responseannotation a
            JOIN consultations_response r ON a.response_id = r.id
            JOIN consultations_question q ON r.question_id = q.id
            WHERE q.consultation_id = %s
        )""",
            [consultation_id],
        )


def delete_responses_in_batches(consultation_id: UUID, batch_size: int = 1000):
    """Delete responses in batches to avoid memory issues"""
    while True:
        with connection.cursor() as cursor:
            cursor.execute(  # nosec B608
                """
            DELETE FROM consultations_response
            WHERE ctid IN (
                SELECT cr.ctid
                FROM consultations_response cr
                JOIN consultations_question cq ON cr.question_id = cq.id
                WHERE cq.consultation_id = %s
                LIMIT %s
            );
            """,
                [consultation_id, batch_size],
            )
            logger.info(f"Deleted {batch_size} responses")

            if cursor.rowcount == 0:
                break


@job("default", timeout=3_600)
def delete_consultation_job(consultation: models.Consultation):
    logger.refresh_context()

    consultation_id = consultation.id
    consultation_title = consultation.title

    try:
        # Re-fetch the consultation to ensure we have a fresh DB connection
        consultation = models.Consultation.objects.get(id=consultation_id)

        # Delete related objects in order to avoid foreign key constraints
        logger.info(
            "Deleting consultation '{consultation_title}' (ID: {consultation_id})",
            consultation_title=consultation_title,
            consultation_id=consultation_id,
        )

        # Delete in dependency order to avoid foreign key violations
        logger.info("Deleting response annotation themes...")
        delete_response_annotation_themes(consultation_id)

        delete_response_related_table("consultations_responseannotation", consultation_id)
        delete_response_related_table("consultations_response_chosen_options", consultation_id)
        delete_response_related_table("consultations_response_read_by", consultation_id)

        logger.info("Deleting responses...")
        delete_responses_in_batches(consultation_id)

        delete_question_related_table("consultations_candidatetheme", consultation_id)
        delete_question_related_table("consultations_selectedtheme", consultation_id)
        delete_question_related_table("consultations_multichoiceanswer", consultation_id)

        delete_respondent_related_table("consultations_respondent_demographics", consultation_id)

        delete_consultation_related_table("consultations_question", consultation_id)
        delete_consultation_related_table("consultations_respondent", consultation_id)

        logger.info("Deleting consultation...")
        consultation.delete()

        logger.info(
            f"Successfully deleted consultation '{consultation_title}' (ID: {consultation_id})"
        )

    except Exception as e:
        logger.error(
            "Error deleting consultation '{consultation_title}' (ID: {consultation_id}): {error}",
            consultation_title=consultation_title,
            consultation_id=consultation_id,
            error=e,
        )
        raise
