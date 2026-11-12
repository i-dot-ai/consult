"""
This is a temporary file to handle synchronising V2 survey import
flow with what find-themes pipeline expects to be available in S3.
"""

import io
import json
import uuid

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.db import transaction
from django.db.models import BooleanField, Case, Count, Prefetch, Value, When
from django.utils.text import slugify

from consultations.models import (
    CONSULTATION_CODE_MAX_LENGTH,
    Consultation,
    Question,
    Response,
)
from consultations.utils.s3 import get_s3_client

logger = settings.LOGGER

INPUTS_PREFIX = "app_data/consultations"
CODE_SUFFIX_LENGTH = 8

# Placeholder the script wrote into responses.jsonl for hybrid respondents
# who answered the closed part but left the open part blank.
NOT_PROVIDED_PLACEHOLDER = "Not Provided"


def assign_consultation_code(consultation: Consultation) -> str:
    """
    Return the consultation's S3 code, assigning one if it doesn't have it yet.

    Consultations created through the V2 setup flow start with code="", as
    the record is created in the database before any pipeline data exists.
    The code doubles as the S3 folder name under app_data/consultations/ and
    is looked up by the candidate-themes import lambda and used by
    export_selected_themes_to_s3, so once assigned it must never change.
    """
    if consultation.code:
        return consultation.code

    with transaction.atomic():
        locked = Consultation.objects.select_for_update().get(pk=consultation.pk)
        if locked.code:
            return locked.code

        base = slugify(consultation.title) or "consultation"
        max_base_length = CONSULTATION_CODE_MAX_LENGTH - (CODE_SUFFIX_LENGTH + 1)
        base = base[:max_base_length].rstrip("-")

        for _ in range(10):
            # Be very sure there is no duplicates
            candidate = f"{base}-{uuid.uuid4().hex[:CODE_SUFFIX_LENGTH]}"
            candidate_exists = Consultation.objects.filter(code=candidate).exists()
            if candidate_exists:
                continue
            break
        else:
            logger.warning(
                "Could not assign consultation code for '{consultation_id}'",
                consultation_id=consultation.id,
            )
            raise RuntimeError(
                f"Could not assign a unique consultation code for '{consultation.id}'"
            )

        locked.code = candidate
        locked.save(update_fields=["code"])

    logger.info(
        "Assigned consultation code={code} to consultation '{consultation_id}'",
        code=candidate,
        consultation_id=consultation.id,
    )
    return candidate


def sync_has_free_text_with_type(consultation: Consultation) -> int:
    """
    Derive has_free_text from the question type so the V1 pipeline contract
    can be trusted when the S3 inputs are rendered:

    - OPEN -> True, CLOSED / DEMOGRAPHIC -> False
    - questions without a type were imported by the V1 pipeline, which set
      has_free_text itself; they keep their stored flag
    """
    return Question.objects.filter(consultation=consultation, type__isnull=False).update(
        has_free_text=Case(
            When(type=Question.QuestionType.OPEN, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
    )


def export_consultation_inputs_to_s3(consultation: Consultation, consultation_code: str) -> int:
    """
    Write the ThemeFinder inputs layout to S3 using the database as the source.

    Reproduces the inputs dump that scripts/setup_consultation.py used to
    build from workbooks before the V2 setup flow existed, so the pipeline
    keeps reading from the same location:

        app_data/consultations/{consultation_code}/inputs/
            question_part_{n}/question.json
            question_part_{n}/responses.jsonl

    Mirrors the rules of the original script:

    - the pipeline discovers questions by folder existence, so questions with
      no responses are omitted entirely
    - only open questions get responses.jsonl (has_free_text is the shared
      flag for both V1 and V2; the V2 setup flow derives it from `type`)
    - hybrid questions keep the script's "Not Provided" placeholder rows:
      a respondent who answered the closed part but left the open part blank
      gets `{"themefinder_id": N, "text": "Not Provided"}` — rows where
      neither part was answered are dropped, as in the script
    - closed/demographic questions keep their question.json but get no
      responses.jsonl, which makes the batch jobs skip them
    - respondents.jsonl and multi_choice.jsonl are not written; they were only
      read by the old S3-to-DB importer, never by the pipeline
    """
    if not consultation_code:
        raise RuntimeError(
            f"Empty consultation code while exporting consultation '{consultation.id}'"
        )

    s3_client = get_s3_client()
    parts_exported = 0

    questions = list(
        consultation.question_set.order_by("number").prefetch_related(
            "multichoiceanswer_set",
            Prefetch(
                "response_set",
                queryset=Response.objects.select_related("respondent")
                .annotate(chosen_option_count=Count("chosen_options"))
                .order_by("respondent__themefinder_id"),
            ),
        )
    )

    closed_part_ids = [
        question.closed_question_id
        for question in questions
        if question.has_free_text and question.closed_question_id
    ]
    closed_respondents: dict[int, set[int]] = {}
    if closed_part_ids:
        for question_id, respondent_id in Response.objects.filter(
            question_id__in=closed_part_ids
        ).values_list("question_id", "respondent_id"):
            closed_respondents.setdefault(question_id, set()).add(respondent_id)

    for question in questions:
        has_free_text = question.has_free_text
        options = [answer.text for answer in question.multichoiceanswer_set.all()]

        closed_respondent_ids: set[int] = set()
        if has_free_text and question.closed_question_id:
            closed_respondent_ids = closed_respondents.get(question.closed_question_id, set())

        rows = [
            (
                response.respondent_id,
                response.respondent.themefinder_id,
                response.text,
                response.chosen_option_count,
            )
            for response in question.response_set.all()
        ]

        payload_rows: list[tuple[int, str]] = []
        if has_free_text:
            for respondent_id, themefinder_id, text, chosen_option_count in rows:
                if themefinder_id is None:
                    logger.warning(
                        "Response without themefinder_id skipped for consultation "
                        "'{consultation_code}', question {question_number}",
                        consultation_code=consultation_code,
                        question_number=question.number,
                    )
                    continue
                if text and text.strip():
                    payload_rows.append((themefinder_id, text))
                elif chosen_option_count > 0 or respondent_id in closed_respondent_ids:
                    payload_rows.append((themefinder_id, NOT_PROVIDED_PLACEHOLDER))

        if not rows:
            continue

        inputs_path = f"{INPUTS_PREFIX}/{consultation_code}/inputs/question_part_{question.number}"

        question_data: dict = {
            "question_number": question.number,
            "question_text": question.text,
            "has_free_text": has_free_text,
        }
        if options:
            question_data["multi_choice_options"] = sorted(
                option for option in options if option != NOT_PROVIDED_PLACEHOLDER
            )

        try:
            s3_client.put_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=f"{inputs_path}/question.json",
                Body=json.dumps(question_data, indent=4),
            )
        except (ClientError, BotoCoreError):
            logger.exception(
                "Failed to export question.json to S3 for consultation "
                "'{consultation_code}', question {question_number}",
                consultation_code=consultation_code,
                question_number=question.number,
            )
            raise

        if payload_rows:
            jsonl_buffer = io.StringIO()
            for themefinder_id, text in payload_rows:
                jsonl_buffer.write(json.dumps({"themefinder_id": themefinder_id, "text": text}))
                jsonl_buffer.write("\n")

            try:
                s3_client.upload_fileobj(
                    io.BytesIO(jsonl_buffer.getvalue().encode("utf-8")),
                    settings.AWS_BUCKET_NAME,
                    f"{inputs_path}/responses.jsonl",
                )
            except (ClientError, BotoCoreError):
                logger.exception(
                    "Failed to export responses.jsonl to S3 for consultation "
                    "'{consultation_code}', question {question_number}",
                    consultation_code=consultation_code,
                    question_number=question.number,
                )
                raise

        parts_exported += 1
        logger.info(
            "Exported question_part_{question_number} to s3://{bucket}/{inputs_path}/ "
            "({responses_count} responses)",
            question_number=question.number,
            bucket=settings.AWS_BUCKET_NAME,
            inputs_path=inputs_path,
            responses_count=len(payload_rows),
        )

    return parts_exported
