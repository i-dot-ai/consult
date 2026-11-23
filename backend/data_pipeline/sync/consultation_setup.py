from uuid import UUID

import tiktoken
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.db import transaction

from authentication.models import User
from consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
)
from data_pipeline import s3
from data_pipeline.models import (
    ConsultationDataBatch,
    QuestionInput,
    RespondentInput,
    ResponseInput,
)
from embeddings import embed_text
from rq_context import job

logger = settings.LOGGER
encoding = tiktoken.encoding_for_model("text-embedding-3-small")
DEFAULT_TIMEOUT_SECONDS = 3_600

# =============================================================================
# S3 LOADERS - Load and validate data from S3
# =============================================================================


def load_respondents_from_s3(consultation_code: str, bucket_name: str) -> list[RespondentInput]:
    """
    Load and validate respondents from S3.

    Args:
        consultation_code: Consultation code
        bucket_name: S3 bucket name
        s3_client: Optional boto3 S3 client

    Returns:
        List of validated RespondentInput objects
    """
    key = f"app_data/consultations/{consultation_code}/inputs/respondents.jsonl"

    logger.info("Loading respondents from {key}", key=key)

    try:
        raw_data = s3.read_jsonl(bucket_name, key)
    except (ClientError, BotoCoreError) as e:
        logger.exception(
            "Failed to load respondents file from S3: bucket={bucket}, key={key}",
            bucket=bucket_name,
            key=key,
        )
        if isinstance(e, ClientError) and e.response["Error"]["Code"] == "NoSuchKey":
            raise ValueError(f"Respondents file not found: {key}") from e
        raise

    respondents = [RespondentInput(**data) for data in raw_data]

    logger.info(
        "Loaded and validated {respondent_count} respondents", respondent_count=len(respondents)
    )
    return respondents


def load_question_from_s3(
    consultation_code: str, question_number: int, bucket_name: str
) -> QuestionInput:
    """
    Load and validate a single question from S3.

    Args:
        consultation_code: Consultation code
        question_number: Question number
        bucket_name: S3 bucket name

    Returns:
        Validated QuestionInput object
    """
    key = f"app_data/consultations/{consultation_code}/inputs/question_part_{question_number}/question.json"

    logger.info(
        "Loading question {question_number} from {key}", question_number=question_number, key=key
    )

    try:
        data = s3.read_json(bucket_name, key)
    except (ClientError, BotoCoreError) as e:
        logger.exception(
            "Failed to load question file from S3: bucket={bucket}, key={key}",
            bucket=bucket_name,
            key=key,
        )
        if isinstance(e, ClientError) and e.response["Error"]["Code"] == "NoSuchKey":
            raise ValueError(f"Question file not found: {key}") from e
        raise

    if data is None:
        raise ValueError(f"Question file not found or empty: {key}")

    # Ensure question_number is set (might not be in the file)
    data["question_number"] = question_number

    question = QuestionInput(**data)

    logger.info("Loaded and validated question {question_number}", question_number=question_number)
    return question


def load_responses_from_s3(
    consultation_code: str,
    question_number: int,
    bucket_name: str,
    file_name: str = "responses.jsonl",
) -> list[ResponseInput]:
    """
    Load and validate one-row-per-answer data for a question from S3.

    Args:
        consultation_code: Consultation code
        question_number: Question number
        bucket_name: S3 bucket name
        file_name: responses.jsonl for an open question, answers.jsonl otherwise

    Returns:
        List of validated ResponseInput objects
    """
    key = f"app_data/consultations/{consultation_code}/inputs/question_part_{question_number}/{file_name}"

    logger.info(
        "Loading responses for question {question_number} from {key}",
        question_number=question_number,
        key=key,
    )

    raw_data = s3.read_jsonl(bucket_name, key, raise_if_missing=False)
    if not raw_data:
        logger.info(
            "No responses found for question {question_number} in S3 at {key}",
            question_number=question_number,
            key=key,
        )
        return []

    responses = []
    for data in raw_data:
        response = ResponseInput(**data)
        if response.text:
            responses.append(response)

    logger.info(
        "Loaded and validated {response_count} responses for question {question_number}",
        response_count=len(responses),
        question_number=question_number,
    )
    return responses


def load_answers_from_s3(
    consultation_code: str, question_number: int, bucket_name: str
) -> list[ResponseInput]:
    """answers.jsonl lists a closed or demographic question's selected options, one per
    line, in the same shape as responses.jsonl."""
    return load_responses_from_s3(
        consultation_code, question_number, bucket_name, file_name="answers.jsonl"
    )


def load_consultation_data_batch(
    consultation_code: str,
    consultation_title: str,
    bucket_name: str | None = None,
) -> ConsultationDataBatch:
    """
    Load and validate base consultation data from S3.

    This orchestrates loading:
    - Respondents
    - Questions
    - Free text responses of open questions
    - Selected options of closed and demographic questions

    Args:
        consultation_code: Consultation code (S3 folder name)
        consultation_title: Display title for the consultation
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)

    Returns:
        Validated ConsultationDataBatch with all data
    """
    if bucket_name is None:
        bucket_name = settings.AWS_BUCKET_NAME

    logger.info(
        "Loading consultation data batch for {consultation_code}",
        consultation_code=consultation_code,
    )

    # Load respondents
    respondents = load_respondents_from_s3(consultation_code, bucket_name)

    # Discover question folders
    inputs_path = f"app_data/consultations/{consultation_code}/inputs/"
    question_folders = s3.get_question_folders(inputs_path, bucket_name)

    if not question_folders:
        raise ValueError(f"No question folders found at {inputs_path}")

    # Extract question numbers from folder paths
    question_numbers = []
    for folder in question_folders:
        # folder looks like: "app_data/.../question_part_1/"
        question_num_str = folder.split("/")[-2].replace("question_part_", "")
        question_numbers.append(int(question_num_str))

    question_numbers.sort()

    # Load questions
    questions = []
    for question_number in question_numbers:
        question = load_question_from_s3(consultation_code, question_number, bucket_name)
        questions.append(question)

    responses_by_question: dict[int, list[ResponseInput]] = {}
    answers_by_question: dict[int, list[ResponseInput]] = {}

    for question in questions:
        if question.type == Question.QuestionType.OPEN:
            responses = load_responses_from_s3(
                consultation_code, question.question_number, bucket_name
            )
            if responses:
                responses_by_question[question.question_number] = responses
        else:
            answers = load_answers_from_s3(consultation_code, question.question_number, bucket_name)
            if answers:
                answers_by_question[question.question_number] = answers

    # Create and validate the batch
    batch = ConsultationDataBatch(
        consultation_code=consultation_code,
        consultation_title=consultation_title,
        respondents=respondents,
        questions=questions,
        responses_by_question=responses_by_question,
        answers_by_question=answers_by_question,
    )

    logger.info(
        "Loaded consultation data batch: {respondent_count} respondents, {question_count} questions, {response_count} total responses",
        respondent_count=len(respondents),
        question_count=len(questions),
        response_count=sum(len(rows) for rows in responses_by_question.values())
        + sum(len(rows) for rows in answers_by_question.values()),
    )

    return batch


# =============================================================================
# IMPORT LOGIC - Create Django models from validated data
# =============================================================================


@transaction.atomic
def import_consultation_data(
    batch: ConsultationDataBatch, user_id: UUID, batch_size: int = 512
) -> UUID:
    """
    Import base consultation data (consultation, respondents, questions, responses) into database.

    This function is idempotent and can be safely re-run. It will update existing
    consultations rather than creating duplicates.

    Base consultation data includes:
    - Consultation definition
    - Respondents
    - Questions, one per demographic field on top of the imported ones
    - Responses: free text, selected options and demographic values

    This does NOT include:
    - Candidate themes (from find-themes job)
    - Response annotations (from assign-themes job)

    Args:
        batch: Validated consultation data batch from S3
        user_id: User ID to associate with consultation

    Returns:
        UUID of created/updated consultation

    Raises:
        User.DoesNotExist: If user_id doesn't exist
    """
    logger.info(
        "Starting consultation data ingestion for {consultation_code}",
        consultation_code=batch.consultation_code,
    )

    # 1. Create or update consultation
    consultation, created = Consultation.objects.get_or_create(
        code=batch.consultation_code,
        defaults={
            "title": batch.consultation_title,
        },
    )

    if not created:
        logger.warning(
            "Consultation {consultation_code} already exists, updating...",
            consultation_code=batch.consultation_code,
        )
        consultation.title = batch.consultation_title
        consultation.save()

    # Add user to consultation
    user = User.objects.get(id=user_id)
    consultation.users.add(user)

    # 2. Create respondents
    _ingest_respondents(consultation, batch.respondents)

    # 3. Create questions, one per demographic field, and link hybrids
    _ingest_questions(
        consultation,
        batch.questions,
        _demographic_fields(batch.respondents, batch.questions),
    )

    # 4. Create responses: free text, selected options and demographic values
    _ingest_responses(consultation, batch, batch_size)

    logger.info(
        "Completed consultation data ingestion for {consultation_code}",
        consultation_code=consultation.code,
    )
    return consultation.id


def _ingest_respondents(consultation: Consultation, respondents: list[RespondentInput]) -> None:
    """
    Create respondents for a consultation.

    This deletes existing respondents for idempotency (cascades to responses).
    """
    logger.info("Ingesting {respondent_count} respondents", respondent_count=len(respondents))

    existing_count = Respondent.objects.filter(consultation=consultation).count()
    if existing_count > 0:
        logger.warning(
            "Deleting {existing_count} existing respondents for idempotency",
            existing_count=existing_count,
        )
        Respondent.objects.filter(consultation=consultation).delete()

    created_respondents = Respondent.objects.bulk_create(
        Respondent(consultation=consultation, themefinder_id=respondent_input.themefinder_id)
        for respondent_input in respondents
    )

    logger.info("Created {respondent_count} respondents", respondent_count=len(created_respondents))


def _demographic_fields(
    respondents: list[RespondentInput], questions: list[QuestionInput]
) -> list[str]:
    """Demographic field names in first-seen order; each becomes a demographic question
    unless question.json already declares one with that text."""
    declared = {
        question.question_text
        for question in questions
        if question.type == Question.QuestionType.DEMOGRAPHIC
    }
    seen: dict[str, None] = {}
    for respondent in respondents:
        seen.update(dict.fromkeys(respondent.demographic_data))
    return [field_name for field_name in seen if field_name not in declared]


def _ingest_questions(
    consultation: Consultation, questions: list[QuestionInput], demographic_fields: list[str]
) -> None:
    """
    Create the imported questions plus one demographic question per demographic field,
    numbered after the imported ones, and link each open question to its closed sibling.

    This deletes existing questions for idempotency (cascades to responses).
    """
    logger.info("Ingesting {question_count} questions", question_count=len(questions))

    existing_count = Question.objects.filter(consultation=consultation).count()
    if existing_count > 0:
        logger.warning(
            "Deleting {existing_count} existing questions for idempotency",
            existing_count=existing_count,
        )
        Question.objects.filter(consultation=consultation).delete()

    questions_to_create = [
        Question(
            consultation=consultation,
            text=question_input.question_text,
            number=question_input.question_number,
            type=question_input.type,
            has_free_text=question_input.type == Question.QuestionType.OPEN,
            has_multiple_choice=question_input.type == Question.QuestionType.CLOSED,
        )
        for question_input in questions
    ]
    next_number = max((question_input.question_number for question_input in questions), default=0)
    for field_name in demographic_fields:
        next_number += 1
        questions_to_create.append(
            Question(
                consultation=consultation,
                text=field_name,
                number=next_number,
                type=Question.QuestionType.DEMOGRAPHIC,
                has_free_text=False,
            )
        )
    created_questions = Question.objects.bulk_create(questions_to_create)

    questions_by_number = {question.number: question for question in created_questions}
    linked_questions = []
    for question_input in questions:
        if question_input.closed_question_number is None:
            continue
        question = questions_by_number[question_input.question_number]
        question.closed_question = questions_by_number[question_input.closed_question_number]
        linked_questions.append(question)
    if linked_questions:
        Question.objects.bulk_update(linked_questions, ["closed_question"])

    logger.info("Created {question_count} questions", question_count=len(created_questions))


def _ingest_responses(
    consultation: Consultation, batch: ConsultationDataBatch, batch_size: int = 512
) -> None:
    """
    Create one Response row per free-text answer, per selected option of a closed or
    demographic question, and per demographic value of a respondent, matching
    themefinder_id to Respondent and question_number to Question.
    """
    logger.info("Ingesting responses")

    respondent_lookup = {
        respondent.themefinder_id: respondent
        for respondent in Respondent.objects.filter(consultation=consultation)
    }

    questions = list(Question.objects.filter(consultation=consultation))
    for question in questions:
        logger.info(
            "Processing responses for question {question_number}", question_number=question.number
        )
        rows: list[tuple[int, str | None]]
        if question.type == Question.QuestionType.OPEN:
            rows = [
                (response.themefinder_id, response.text)
                for response in batch.responses_by_question.get(question.number, [])
            ]
        elif (
            question.type == Question.QuestionType.DEMOGRAPHIC
            and question.number not in batch.answers_by_question
        ):
            rows = [
                (respondent.themefinder_id, value)
                for respondent in batch.respondents
                for value in respondent.demographic_data.get(question.text, [])
            ]
        else:
            # closed questions, and demographic questions that brought their own answers.jsonl
            rows = [
                (answer.themefinder_id, answer.text)
                for answer in batch.answers_by_question.get(question.number, [])
            ]
            if not rows and question.type == Question.QuestionType.CLOSED:
                logger.warning(
                    "Closed question {question_number} has no answers.jsonl rows",
                    question_number=question.number,
                )

        created = _create_response_rows(
            question,
            rows,
            respondent_lookup,
            batch_size,
            free_text=question.type == Question.QuestionType.OPEN,
        )
        logger.info(
            "Saved {response_count} responses for question {question_number}",
            response_count=created,
            question_number=question.number,
        )

    # Only once every question has its rows: a hybrid's open part counts the respondents
    # of its closed sibling, whatever number that sibling carries
    for question in questions:
        question.update_response_counts()

    logger.info("Completed response ingestion")


def _create_response_rows(
    question: Question,
    rows: list[tuple[int, str | None]],
    respondent_lookup: dict[int, Respondent],
    batch_size: int,
    free_text: bool,
) -> int:
    """Skips unknown respondents and blank or placeholder texts; free text is truncated
    past the embedding limit and saved in token-bounded batches."""
    responses_to_create: list[Response] = []
    max_total_tokens = 100_000
    max_tokens_per_text = 8192
    total_tokens = 0
    created = 0

    for themefinder_id, text in rows:
        respondent = respondent_lookup.get(themefinder_id)
        if respondent is None:
            logger.warning("No respondent found for themefinder_id {tf_id}", tf_id=themefinder_id)
            continue

        text = (text or "").strip()
        if text in ("", "Not Provided", "-"):
            continue

        token_count = 0
        if free_text:
            tokens = encoding.encode(text)
            if len(tokens) > max_tokens_per_text:
                logger.warning("Truncated text for themefinder_id: {tf_id}", tf_id=themefinder_id)
                tokens = tokens[:max_tokens_per_text]
                text = encoding.decode(tokens)
            token_count = len(tokens)

        if total_tokens + token_count > max_total_tokens or len(responses_to_create) >= batch_size:
            created += _save_response_rows(responses_to_create, free_text)
            responses_to_create = []
            total_tokens = 0

        responses_to_create.append(
            Response(
                respondent=respondent,
                question=question,
                text=text,
                free_text=text if free_text else None,
            )
        )
        total_tokens += token_count

    return created + _save_response_rows(responses_to_create, free_text)


def _save_response_rows(responses: list[Response], free_text: bool) -> int:
    created_responses = Response.objects.bulk_create(responses)
    if free_text:
        # bulk_create skips the post_save signal that fills the search vector
        for response in created_responses:
            response.save()
    return len(created_responses)


# =============================================================================
# ASYNC JOBS - Background processing
# =============================================================================


@job("default", timeout=DEFAULT_TIMEOUT_SECONDS)
def create_embeddings_for_question(question_id: UUID) -> None:
    """
    Create embeddings for all responses to a question.

    This is designed to be run as an async job via django-rq.

    Args:
        question_id: UUID of the question
    """
    from django.contrib.postgres.search import SearchVector

    queryset = Response.objects.filter(question_id=question_id, free_text__isnull=False)
    total = queryset.count()
    batch_size = 1_000

    logger.info(
        "Creating embeddings for {total} responses in question {question_id}",
        total=total,
        question_id=question_id,
    )

    for i in range(0, total, batch_size):
        responses = queryset.order_by("id")[i : i + batch_size]

        free_texts = [
            f"Question: {response.question.text} \nAnswer: {response.free_text}"
            for response in responses
        ]

        embeddings = embed_text(free_texts)

        for response, embedding in zip(responses, embeddings):
            response.embedding = embedding
            response.search_vector = SearchVector("free_text")

        Response.objects.bulk_update(responses, ["embedding", "search_vector"])

        logger.info(
            "Created embeddings for batch {batch_num} of question {question_id}",
            batch_num=i // batch_size + 1,
            question_id=question_id,
        )

    logger.info("Completed embedding creation for question {question_id}", question_id=question_id)


# =============================================================================
# ORCHESTRATION - High-level workflow functions
# =============================================================================


def import_consultation_from_s3(
    consultation_code: str,
    consultation_title: str,
    user_id: UUID,
    enqueue_embeddings: bool = False,  # Whether to enqueue embedding jobs after import (default False for consultation setup for now)
    batch_size: int = 512,
) -> UUID:
    """
    Import consultation base data from S3.

    This orchestrates:
    1. Loading data from S3
    2. Validating with Pydantic
    3. Ingesting into Django models
    4. Optionally enqueueing async jobs for embeddings

    Args:
        consultation_code: S3 folder code
        consultation_title: Display name
        user_id: User ID to associate
        enqueue_embeddings: Whether to enqueue embedding jobs (default True)

    Returns:
        Consultation UUID
    """
    logger.info("Starting S3 import for {consultation_code}", consultation_code=consultation_code)

    # Load and validate data from S3
    batch = load_consultation_data_batch(
        consultation_code=consultation_code,
        consultation_title=consultation_title,
    )

    # Import consultation data into database
    consultation_id = import_consultation_data(batch, user_id, batch_size)

    # Enqueue async jobs for embeddings
    if enqueue_embeddings:
        consultation = Consultation.objects.get(id=consultation_id)

        for question in Question.objects.filter(consultation=consultation):
            if question.has_free_text:
                logger.info(
                    "Enqueueing embedding job for question {question_number}",
                    question_number=question.number,
                )
                create_embeddings_for_question.enqueue(question.id)

    logger.info("Completed S3 import for {consultation_code}", consultation_code=consultation_code)
    return consultation_id
