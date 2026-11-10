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

    Does not modify the passed instance; the code is persisted on the
    consultation row and returned, so callers thread the returned value
    through the rest of the kickoff.
    """
    if consultation.code:
        return consultation.code

    with transaction.atomic():
        # Lock the row so two concurrent kickoffs of the same consultation
        # cannot both pass the blank check and assign different codes.
        locked = Consultation.objects.select_for_update().get(pk=consultation.pk)
        if locked.code:
            return locked.code

        base = slugify(consultation.title) or "consultation"
        max_base_length = CONSULTATION_CODE_MAX_LENGTH - (CODE_SUFFIX_LENGTH + 1)
        base = base[:max_base_length].rstrip("-")

        # The uuid suffix makes collisions vanishingly unlikely; retry rather
        # than risk two consultations sharing an S3 folder.
        for _ in range(10):
            candidate = f"{base}-{uuid.uuid4().hex[:CODE_SUFFIX_LENGTH]}"
            if not Consultation.objects.filter(code=candidate).exists():
                break
        else:
            raise RuntimeError(
                f"Could not assign a unique consultation code for '{consultation.title}'"
            )

        locked.code = candidate
        locked.save(update_fields=["code"])

    logger.info(
        "Assigned consultation code={code} to consultation '{consultation_title}'",
        code=candidate,
        consultation_title=consultation.title,
    )
    return candidate


def sync_has_free_text_with_type(consultation: Consultation) -> int:
    """
    Derive has_free_text from the question type so the V1 pipeline contract
    can be trusted when the S3 inputs are rendered:

    - OPEN -> True, CLOSED / DEMOGRAPHIC -> False
    - questions without a type were imported by the V1 pipeline, which set
      has_free_text itself; they keep their stored flag

    The V2 setup flow types questions without maintaining the flag, and
    CONSULT-HY showed the pipeline failing on the disagreement, so this runs
    at find-themes kickoff, before the mirror renders the S3 inputs and
    before the handler guards on has_free_text.
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

    Later pipeline steps read from the same folders (assign-themes reads
    themes.csv written into them by export_selected_themes_to_s3), so this
    must run before find-themes is kicked off.

    Args:
        consultation: Consultation to export
        consultation_code: The S3 folder name for the consultation, as
            returned by assign_consultation_code

    Requires:
        The pipeline must not start before this returns, so it runs
        synchronously in the caller (no RQ job). S3 pushes at this scale
        were historically <60 seconds regardless of consultation size;
        revisit if real consultations approach that.

    Returns:
        Number of question_part folders written

    Raises:
        RuntimeError: If the consultation code is empty
    """
    if not consultation_code:
        raise RuntimeError(
            f"Empty consultation code while exporting consultation '{consultation.title}'"
        )

    s3_client = get_s3_client()
    parts_exported = 0

    # Prefetch everything the loop needs up front: the response rows keep
    # their annotation and ordering through the Prefetch queryset, and
    # select_related("respondent") keeps the themefinder_id traversal query-free.
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

    # A respondent answered the closed part of a hybrid question either via
    # chosen_options on the response itself or via a response on the linked
    # closed question (both shapes are valid under ADR-0006); collect the
    # second shape for every free-text question in one query.
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

        # Only open questions get a responses.jsonl; closed and demographic
        # questions may still carry text in their responses (e.g. the selected
        # option), which must not be theme-found.
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
                    # V1 rule: hybrid respondents who answered the closed part
                    # but left the open part blank still got a placeholder row.
                    payload_rows.append((themefinder_id, NOT_PROVIDED_PLACEHOLDER))
                # Rows where neither part was answered were dropped by the
                # script and are dropped here too.

        if not rows:
            # Old rule: no responses at all means no question folder; the
            # pipeline discovers questions by folder existence.
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
                # Transfer-manager upload: retries transient failures, and
                # bodies above boto3's multipart threshold are chunked
                # instead of being a single put request.
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
