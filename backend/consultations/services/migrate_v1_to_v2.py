"""V1 to V2 data migration for single consultations (PRO-980).

The migration moves one consultation at a time from the legacy V1 schema
(`Response.free_text`, `has_free_text`/`has_multiple_choice`,
`DemographicOption` + `Respondent.demographics`) to the V2 schema
(`Response.text`, `Question.type`, demographics as responses on demographic
questions). Work is bounded per consultation the same way as clone
(consultations/services/clone.py).

Steps, each written to be idempotent and wrapped in a single transaction:

0. ``_mark_schema_origin`` consultations with a data_source already set went
   through the V2 provider-selection flow and are marked V2; the rest are V1
1. ``_fill_response_text`` copy free_text -> text
2. ``_backfill_question_types`` flag pair -> Question.type
3. ``_convert_multiple_choice_to_responses`` chosen options -> one response
   row per selected option on closed questions
4. ``_backfill_data_source`` default the data source to CitizenSpace
5. ``_refresh_denormalised_counts`` recalculate response/answer counts
6. ``_assign_stage`` advance the stage to match the artifacts on record
7. ``_update_survey_import_status`` mark the setup concluded where provable
"""

from typing import Any
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from consultations.models import (
    CandidateTheme,
    Consultation,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    SelectedTheme,
)
from consultations.services.setup_status import update_survey_import_status_for_questions
from rq_context import job

logger = settings.LOGGER

_RESPONSE_ROW_BATCH_SIZE = 1000


def audit_consultation(consultation: Consultation) -> dict[str, int]:
    """Count the V1-shaped data the migration would change, without writing."""
    questions = consultation.question_set
    return {
        "responses_missing_text": Response.objects.filter(
            question__consultation=consultation, free_text__isnull=False, text__isnull=True
        ).count(),
        "questions_without_type": questions.filter(type__isnull=True).count(),
        "questions_open_only": questions.filter(
            has_free_text=True, has_multiple_choice=False, type__isnull=True
        ).count(),
        "questions_closed_only": questions.filter(
            has_free_text=False, has_multiple_choice=True, type__isnull=True
        ).count(),
        "questions_hybrid": questions.filter(
            has_free_text=True, has_multiple_choice=True, type__isnull=True
        ).count(),
        "questions_without_flags": questions.filter(
            has_free_text=False, has_multiple_choice=False, type__isnull=True
        ).count(),
        "multiple_choice_links": Response.chosen_options.through.objects.filter(
            response__question__consultation=consultation
        ).count(),
        "multi_choice_answers": MultiChoiceAnswer.objects.filter(
            question__consultation=consultation
        ).count(),
        "demographic_options": DemographicOption.objects.filter(consultation=consultation).count(),
        "respondent_demographic_links": Respondent.demographics.through.objects.filter(
            respondent__consultation=consultation
        ).count(),
        "missing_data_source": 1 if consultation.data_source is None else 0,
    }


@transaction.atomic
def migrate_consultation_to_v2(consultation: Consultation) -> Consultation:
    """Migrate one consultation's data from the V1 schema to the V2 schema.

    Idempotent: already-migrated consultations return unchanged, re-runs
    after a failure can never duplicate rows, and consultations that already
    went through the V2 provider-selection flow (data_source set) are marked
    as V2 and skipped instead of migrated.
    """
    if consultation.migrated_at is not None:
        logger.info(
            "Consultation {consultation_id} was already migrated at {migrated_at}; skipping",
            consultation_id=consultation.id,
            migrated_at=consultation.migrated_at,
        )
        return consultation

    _mark_schema_origin(consultation)
    if not consultation.is_v1:
        logger.info(
            "Consultation {consultation_id} already has a survey provider; "
            "marked as V2, nothing to migrate",
            consultation_id=consultation.id,
        )
        return consultation

    _fill_response_text(consultation)
    _backfill_question_types(consultation)
    _convert_multiple_choice_to_responses(consultation)
    _backfill_data_source(consultation)
    _refresh_denormalised_counts(consultation)
    _assign_stage(consultation)
    _update_survey_import_status(consultation)

    consultation.migrated_at = timezone.now()
    consultation.save(update_fields=["migrated_at"])
    logger.info(
        "Successfully migrated consultation {consultation_id} to the V2 schema",
        consultation_id=consultation.id,
    )
    return consultation


def _mark_schema_origin(consultation: Consultation) -> None:
    """Record whether the consultation's data is V1 or V2 shaped.

    Consultations that already have data_source set went through the V2
    provider-selection flow and are marked V2 (is_v1=False); anything
    without one is marked V1 (is_v1=True). Runs before _backfill_data_source
    so the backfill cannot influence the classification, and only for
    consultations that are not yet migrated (the caller gates this) so
    migrated V1 consultations keep their V1 origin.
    """
    marked_as_v1 = consultation.data_source is None
    consultation.is_v1 = marked_as_v1
    consultation.save(update_fields=["is_v1"])
    logger.info(
        "Consultation {consultation_id} marked as {data_schema}",
        consultation_id=consultation.id,
        data_schema="V1" if marked_as_v1 else "V2",
    )


def _fill_response_text(consultation: Consultation) -> None:
    """Copy Response.free_text into Response.text.

    One bulk UPDATE, text = free_text, for every response where text IS NULL
    and free_text IS NOT NULL and not empty (empty responses were already
    normalised to NULL by migration 0101). free_text stays populated so V1
    API consumers keep working until they move to text, mirroring the dual
    write in the V2 importer (ingest/consultation_file.py).

    update() does not fire the search-vector signal, which is correct here:
    the search vector was built from free_text (the identical value) when
    the response was embedded, so re-deriving it would be no-op.
    """
    copied = (
        Response.objects.filter(
            question__consultation=consultation,
            text__isnull=True,
            free_text__isnull=False,
        )
        .exclude(free_text="")
        .update(text=F("free_text"))
    )
    logger.info(
        "Copied free_text into text for {response_rows} responses on {consultation_id}",
        response_rows=copied,
        consultation_id=consultation.id,
    )


def _backfill_question_types(consultation: Consultation) -> None:
    """Derive Question.type from has_free_text / has_multiple_choice.

    has_free_text=True only       -> Question.QuestionType.OPEN
    has_multiple_choice=True only -> Question.QuestionType.CLOSED
    both (hybrid)                 -> the original question becomes the OPEN
                                     one (keeps id, number, text,
                                     annotations and embeddings) and a new
                                     sibling CLOSED question is created to
                                     hold the options; the original's
                                     closed_question FK points at the
                                     sibling (the open question holds the
                                     FK; see api_v2/serializers.py rules)
    neither                       -> prod audit (2026-11-16) found zero
                                     occurrences; left untyped and logged
                                     so a straggler import can never be
                                     silently mis-typed

    Only untyped questions are processed, and status follows
    QuestionSetupSerializer.update: setting a type marks the question
    CONFIGURED. survey_import_status is deliberately untouched here.
    """
    next_number = (
        consultation.question_set.order_by("-number").values_list("number", flat=True).first()
        or 0
    ) + 1
    for question in consultation.question_set.filter(type__isnull=True).order_by("number"):
        if question.has_multiple_choice and question.has_free_text:
            _split_hybrid_question(question, next_number)
            next_number += 1
        elif question.has_multiple_choice:
            _set_question_type(question, Question.QuestionType.CLOSED)
        elif question.has_free_text:
            _set_question_type(question, Question.QuestionType.OPEN)
        else:
            logger.warning(
                "Question {question_id} on consultation {consultation_id} has neither free "
                "text nor multiple choice; leaving it untyped for manual review",
                question_id=question.id,
                consultation_id=consultation.id,
            )


def _set_question_type(question: Question, question_type: Any) -> None:
    # ``QuestionType`` members are ``str`` subclasses at runtime, but without
    # django-stubs mypy infers the raw (value, label) tuples, so the
    # parameter is deliberately Any.
    question.type = question_type
    question.status = Question.ThemeStatus.CONFIGURED
    question.save(update_fields=["type", "status"])


def _split_hybrid_question(question: Question, number: int) -> Question:
    """Promote the original question to OPEN and create its CLOSED sibling.

    The sibling inherits the question wording and option values and is
    appended at the end of the question order (numbers are ints, so it
    cannot slot in beside the original). The caller threads the next free
    question number so a consultation with many hybrids does not pay a
    max(number) query per sibling.
    """
    consultation = question.consultation
    option_texts = list(question.multichoiceanswer_set.values_list("text", flat=True))
    if not option_texts:
        logger.warning(
            "Hybrid question {question_id} has no multi-choice options to inherit",
            question_id=question.id,
        )
    closed_question = Question(
        consultation=consultation,
        text=question.text,
        number=number,
        has_free_text=False,
        has_multiple_choice=True,
        type=Question.QuestionType.CLOSED,
        status=Question.ThemeStatus.CONFIGURED,
    )
    closed_question.save()
    MultiChoiceAnswer.objects.bulk_create(
        [MultiChoiceAnswer(question=closed_question, text=text) for text in option_texts]
    )

    question.type = Question.QuestionType.OPEN
    question.status = Question.ThemeStatus.CONFIGURED
    question.closed_question = closed_question
    question.save(update_fields=["type", "status", "closed_question"])
    return closed_question


def _convert_multiple_choice_to_responses(consultation: Consultation) -> None:
    """Turn selected options into one Response row per selected option.

    For every v1 response carrying chosen_options, create one Response row
    per selected option with text = the option text. Rows land on the
    question that became CLOSED: the question itself for closed-only
    questions, or the closed sibling for hybrids (the original question
    became OPEN in _backfill_question_types). The original row stays
    untouched as the respondent's free-text row, and chosen_options stays
    populated until V1 consumers move off it, so a respondent who chose no
    options simply gets no new rows.

    Dedupes on (question, respondent, text), so re-runs can never duplicate
    rows. bulk_create does not fire the search-vector signal, which is what
    we want: option rows carry no embedding or search vector.
    """
    questions = {question.id: question for question in consultation.question_set.all()}

    def target_question_id(source_question_id):
        question = questions[source_question_id]
        if question.type == Question.QuestionType.CLOSED:
            return question.id
        if question.type == Question.QuestionType.OPEN and question.closed_question_id:
            return question.closed_question_id
        logger.warning(
            "Skipping chosen options on question {question_id}: it has no V2 question to "
            "receive them",
            question_id=question.id,
        )
        return None

    # Option rows only ever land on closed questions, so the dedupe set can
    # ignore every other response in the consultation.
    existing_pairs = set(
        Response.objects.filter(
            question__consultation=consultation, question__type=Question.QuestionType.CLOSED
        ).values_list("question_id", "respondent_id", "text")
    )

    links = (
        Response.chosen_options.through.objects.filter(
            response__question__consultation=consultation
        )
        .select_related("response", "multichoiceanswer")
        .only(
            "response__question_id",
            "response__respondent_id",
            "multichoiceanswer__text",
        )
        .iterator(chunk_size=_RESPONSE_ROW_BATCH_SIZE)
    )

    # Rows stream in and flush to the database every batch, so memory stays
    # bounded for consultations with millions of option links.
    created = 0
    batch: list[Response] = []
    for link in links:
        target_id = target_question_id(link.response.question_id)
        option_text = link.multichoiceanswer.text
        if target_id is None or not option_text:
            continue
        candidate = (target_id, link.response.respondent_id, option_text)
        if candidate in existing_pairs:
            continue
        existing_pairs.add(candidate)
        batch.append(
            Response(
                question_id=target_id,
                respondent_id=link.response.respondent_id,
                text=option_text,
            )
        )
        if len(batch) == _RESPONSE_ROW_BATCH_SIZE:
            Response.objects.bulk_create(batch, batch_size=_RESPONSE_ROW_BATCH_SIZE)
            created += len(batch)
            batch = []

    if batch:
        Response.objects.bulk_create(batch, batch_size=_RESPONSE_ROW_BATCH_SIZE)
        created += len(batch)
    if created:
        logger.info(
            "Created {response_rows} option response rows for consultation {consultation_id}",
            response_rows=created,
            consultation_id=consultation.id,
        )


def _backfill_data_source(consultation: Consultation) -> None:
    """Default the data source for pre-survey-import consultations.

    Runs after _mark_schema_origin, so consultations that already carry a
    provider keep it, and freshly classified V1 consultations get
    CitizenSpace (to be revisited later, see PRO-980).
    """
    consultation.data_source = (
        consultation.data_source or Consultation.DataSource.CITIZEN_SPACE
    )
    consultation.save(update_fields=["data_source"])


def _refresh_denormalised_counts(consultation: Consultation) -> None:
    """Recalculate the denormalised response counts after rows are moved.

    Original questions keep their v1 semantics: free_text and chosen_options
    stay populated (decision: keep all), so Question.update_response_counts
    and MultiChoiceAnswer.update_response_counts reproduce the same numbers
    as before the migration.

    New closed siblings (created by _split_hybrid_question) have no v1
    representation of their answers: their counts are derived from the
    per-option Response rows, counting distinct respondents — the same thing
    the v2 list endpoint and demographics aggregation read.
    """
    questions = list(consultation.question_set.all())
    sibling_ids = {
        question.closed_question_id for question in questions if question.closed_question_id
    }

    for question in questions:
        if question.id in sibling_ids:
            option_rows = question.response_set.filter(text__isnull=False).exclude(text="")
            respondent_count = option_rows.values("respondent_id").distinct().count()
            question.total_response_count = respondent_count
            question.multi_choice_response_count = respondent_count
            question.free_text_response_count = 0
            question.save(
                update_fields=[
                    "total_response_count",
                    "multi_choice_response_count",
                    "free_text_response_count",
                ]
            )
        else:
            question.update_response_counts()
        if question.multichoiceanswer_set.exists():
            MultiChoiceAnswer.update_response_counts(question)


def _assign_stage(consultation: Consultation) -> None:
    """Advance the consultation's stage to match its data.

    The v1 stages describe what has already happened to a consultation, and
    the artifacts on record identify exactly that (user decision):

    - ResponseAnnotations exist -> assigning themes has run -> ANALYSIS
    - SelectedTheme (human-approved themes) exist -> ASSIGNING_THEMES
    - CandidateTheme (AI themes) exist -> FINALISING_THEMES
    - Responses exist -> FINDING_THEMES
    - nothing -> leave the existing stage

    Only ever moves a consultation forward, never back.
    """
    stage_rank = {stage: rank for rank, stage in enumerate(Consultation.Stage.values)}
    new_stage = consultation.stage
    for has_evidence, stage in (
        (
            ResponseAnnotation.objects.filter(
                response__question__consultation=consultation
            ).exists(),
            Consultation.Stage.ANALYSIS,
        ),
        (
            SelectedTheme.objects.filter(question__consultation=consultation).exists(),
            Consultation.Stage.ASSIGNING_THEMES,
        ),
        (
            CandidateTheme.objects.filter(question__consultation=consultation).exists(),
            Consultation.Stage.FINALISING_THEMES,
        ),
        (
            Response.objects.filter(question__consultation=consultation).exists(),
            Consultation.Stage.FINDING_THEMES,
        ),
    ):
        if has_evidence and stage_rank[stage] > stage_rank[new_stage]:
            new_stage = stage
    if new_stage != consultation.stage:
        consultation.stage = new_stage
        consultation.save(update_fields=["stage"])


def _update_survey_import_status(consultation: Consultation) -> None:
    """Record the consultation's data setup as concluded where provable.

    Applies the system's own completion rule (questions exist, none untyped)
    so later edits through v2 recompute to the same value. A consultation
    containing a neither-flag straggler stays PENDING_QUESTIONS instead of
    silently claiming completion, inviting human attention (user decision:
    stage assignment above already protects the frontend view for it).
    """
    update_survey_import_status_for_questions(consultation)


# Migrations of the largest consultations take hours (millions of option and
# demographic response rows), so the timeout is deliberately generous. The
# job is idempotent and fully transactional: on timeout the transaction rolls
# back and the job can simply be re-run.
@job("default", timeout=14400)
def migrate_v1_consultation_job(consultation_id: UUID) -> UUID:
    """
    RQ job wrapper so the django admin action can migrate in the background.
    """
    consultation = Consultation.objects.get(id=consultation_id)
    migrated = migrate_consultation_to_v2(consultation)
    return migrated.id
