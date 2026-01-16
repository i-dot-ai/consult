import logging
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django_rq import job

from consultation_analyser.consultations import models
from consultation_analyser.consultations.dummy_data import (
    create_dummy_consultation_from_yaml,
    create_dummy_consultation_from_yaml_job,
)
from consultation_analyser.consultations.export_user_theme import export_user_theme_job
from consultation_analyser.hosting_environment import HostingEnvironment

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


def index(request: HttpRequest) -> HttpResponse:
    logger.refresh_context()

    if request.POST:
        try:
            if request.POST.get("generate_dummy_consultation") is not None:
                consultation = create_dummy_consultation_from_yaml()
                user = request.user
                consultation.users.add(user)
                messages.success(request, "A dummy consultation has been generated")
            elif request.POST.get("generate_giant_dummy_consultation") is not None:
                n = 100000
                consultation = models.Consultation.objects.create(
                    title=f"Giant dummy consultation - {n} respondents"
                )
                user = request.user
                consultation.users.add(user)
                create_dummy_consultation_from_yaml_job.delay(
                    number_respondents=n, consultation=consultation
                )
                messages.success(
                    request,
                    "A giant dummy consultation is being created - see progress in the Django RQ dashboard",
                )
        except RuntimeError as error:
            messages.error(request, error.args[0])
    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations, "production_env": HostingEnvironment.is_production()}
    return render(request, "support_console/consultations/index.html", context=context)


def delete(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    logger.refresh_context()

    consultation = models.Consultation.objects.get(id=consultation_id)
    context = {
        "consultation": consultation,
    }

    if request.POST:
        if "confirm_deletion" in request.POST:
            delete_consultation_job.delay(consultation=consultation)
            messages.success(
                request,
                "The consultation has been sent for deletion - check queue dashboard for progress",
            )
            return redirect("/support/consultations/")

    return render(request, "support_console/consultations/delete.html", context=context)


def show(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    logger.refresh_context()

    consultation = models.Consultation.objects.get(id=consultation_id)
    questions = models.Question.objects.filter(consultation=consultation).order_by("number")

    context = {
        "consultation": consultation,
        "users": consultation.users.all(),
        "questions": questions,
    }
    return render(request, "support_console/consultations/show.html", context=context)


def export_consultation_theme_audit(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    logger.refresh_context()

    consultation = get_object_or_404(models.Consultation, id=consultation_id)
    questions = models.Question.objects.filter(
        consultation=consultation, has_free_text=True
    ).order_by("number")

    question_items = [{"value": q.id, "text": f"Question {q.number} - {q.text}"} for q in questions]

    context = {
        "consultation": consultation,
        "question_parts_items": question_items,  # Keep the same template variable name
        "bucket_name": settings.AWS_BUCKET_NAME,
        "environment": settings.ENVIRONMENT,
    }

    if request.method == "POST":
        s3_key = request.POST.get("s3_key", "")
        question_ids = request.POST.getlist("question_parts")  # Keep the same form field name
        for id in question_ids:
            try:
                logging.info("Exporting theme audit data - sending to queue")
                export_user_theme_job.delay(question_id=UUID(id), s3_key=s3_key)
            except Exception as e:
                messages.error(request, e)
                return render(request, "support_console/consultations/export_audit.html", context)

        messages.success(
            request,
            "Consultation theme audit export started for question - see Django RQ dashboard for progress",
        )
        return redirect("/support/consultations/")

    return render(request, "support_console/consultations/export_audit.html", context)


def delete_question(request: HttpRequest, consultation_id: UUID, question_id: UUID) -> HttpResponse:
    """Delete a question from a consultation"""
    logger.refresh_context()

    question = models.Question.objects.get(consultation__id=consultation_id, id=question_id)
    context = {
        "question": question,
        "consultation": question.consultation,
    }

    if request.POST:
        if "confirm_deletion" in request.POST:
            question.delete()
            messages.success(request, "The question has been deleted")
            return redirect(f"/support/consultations/{consultation_id}/")
        else:
            return redirect(f"/support/consultations/{consultation_id}/")
    return render(request, "support_console/question_parts/delete.html", context=context)
