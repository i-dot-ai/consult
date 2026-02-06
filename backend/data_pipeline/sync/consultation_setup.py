from typing import Dict, List, Optional
from uuid import UUID

import boto3
import tiktoken
from django.conf import settings
from django.db import transaction
from django_rq import get_queue

import backend.data_pipeline.s3 as s3
from backend.authentication.models import User
from backend.consultations.models import (
    Consultation,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
)
from backend.data_pipeline.models import (
    ConsultationDataBatch,
    MultiChoiceInput,
    QuestionInput,
    RespondentInput,
    ResponseInput,
)
from backend.embeddings import embed_text

logger = settings.LOGGER
encoding = tiktoken.encoding_for_model("text-embedding-3-small")
DEFAULT_TIMEOUT_SECONDS = 3_600


# =============================================================================
# S3 LOADERS - Load and validate data from S3
# =============================================================================


def load_respondents_from_s3(
    consultation_code: str, bucket_name: str, s3_client=None
) -> List[RespondentInput]:
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

    raw_data = s3.read_jsonl(bucket_name, key, s3_client)

    respondents = [RespondentInput(**data) for data in raw_data]

    logger.info(
        "Loaded and validated {respondent_count} respondents", respondent_count=len(respondents)
    )
    return respondents


def load_question_from_s3(
    consultation_code: str, question_number: int, bucket_name: str, s3_client=None
) -> QuestionInput:
    """
    Load and validate a single question from S3.

    Args:
        consultation_code: Consultation code
        question_number: Question number
        bucket_name: S3 bucket name
        s3_client: Optional boto3 S3 client

    Returns:
        Validated QuestionInput object
    """
    key = f"app_data/consultations/{consultation_code}/inputs/question_part_{question_number}/question.json"

    logger.info(
        "Loading question {question_number} from {key}", question_number=question_number, key=key
    )

    data = s3.read_json(bucket_name, key, s3_client)

    if data is None:
        raise ValueError(f"Question file not found or empty: {key}")

    # Ensure question_number is set (might not be in the file)
    data["question_number"] = question_number

    question = QuestionInput(**data)

    logger.info("Loaded and validated question {question_number}", question_number=question_number)
    return question


def load_responses_from_s3(
    consultation_code: str, question_number: int, bucket_name: str, s3_client=None
) -> List[ResponseInput]:
    """
    Load and validate free text responses for a question from S3.

    Args:
        consultation_code: Consultation code
        question_number: Question number
        bucket_name: S3 bucket name
        s3_client: Optional boto3 S3 client

    Returns:
        List of validated ResponseInput objects
    """
    key = f"app_data/consultations/{consultation_code}/inputs/question_part_{question_number}/responses.jsonl"

    logger.info(
        "Loading responses for question {question_number} from {key}",
        question_number=question_number,
        key=key,
    )

    raw_data = s3.read_jsonl(bucket_name, key, s3_client, raise_if_missing=False)

    responses = []
    for data in raw_data:
        # Only include responses that have text
        if data.get("text"):
            responses.append(ResponseInput(**data))

    logger.info(
        "Loaded and validated {response_count} responses for question {question_number}",
        response_count=len(responses),
        question_number=question_number,
    )
    return responses


def load_multi_choice_from_s3(
    consultation_code: str, question_number: int, bucket_name: str, s3_client=None
) -> List[MultiChoiceInput]:
    """
    Load and validate multi-choice selections for a question from S3.

    Args:
        consultation_code: Consultation code
        question_number: Question number
        bucket_name: S3 bucket name
        s3_client: Optional boto3 S3 client

    Returns:
        List of validated MultiChoiceInput objects
    """
    key = f"app_data/consultations/{consultation_code}/inputs/question_part_{question_number}/multi_choice.jsonl"

    logger.info(
        "Loading multi-choice data for question {question_number} from {key}",
        question_number=question_number,
        key=key,
    )

    raw_data = s3.read_jsonl(bucket_name, key, s3_client, raise_if_missing=False)

    multi_choices = []
    for data in raw_data:
        # Only include if they have options selected
        if data.get("options"):
            multi_choices.append(MultiChoiceInput(**data))

    logger.info(
        "Loaded and validated {multi_choice_count} multi-choice responses for question {question_number}",
        multi_choice_count=len(multi_choices),
        question_number=question_number,
    )
    return multi_choices


def load_consultation_data_batch(
    consultation_code: str,
    consultation_title: str,
    bucket_name: Optional[str] = None,
) -> ConsultationDataBatch:
    """
    Load and validate base consultation data from S3.

    This orchestrates loading:
    - Respondents
    - Questions
    - Free text responses
    - Multi-choice selections

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

    s3_client = boto3.client("s3")

    # Load respondents
    respondents = load_respondents_from_s3(consultation_code, bucket_name, s3_client)

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
        question = load_question_from_s3(consultation_code, question_number, bucket_name, s3_client)
        questions.append(question)

    # Load responses and multi-choice data
    responses_by_question: Dict[int, List[ResponseInput]] = {}
    multi_choice_by_question: Dict[int, List[MultiChoiceInput]] = {}

    for question_number in question_numbers:
        # Load free text responses
        responses = load_responses_from_s3(
            consultation_code, question_number, bucket_name, s3_client
        )
        if responses:
            responses_by_question[question_number] = responses

        # Load multi-choice data
        multi_choices = load_multi_choice_from_s3(
            consultation_code, question_number, bucket_name, s3_client
        )
        if multi_choices:
            multi_choice_by_question[question_number] = multi_choices

    # Create and validate the batch
    batch = ConsultationDataBatch(
        consultation_code=consultation_code,
        consultation_title=consultation_title,
        respondents=respondents,
        questions=questions,
        responses_by_question=responses_by_question,
        multi_choice_by_question=multi_choice_by_question,
    )

    logger.info(
        "Loaded consultation data batch: {respondent_count} respondents, {question_count} questions, {response_count} total responses",
        respondent_count=len(respondents),
        question_count=len(questions),
        response_count=sum(len(r) for r in responses_by_question.values()),
    )

    return batch


# =============================================================================
# IMPORT LOGIC - Create Django models from validated data
# =============================================================================


@transaction.atomic
def import_consultation_data(
    batch: ConsultationDataBatch, user_id: UUID, batch_size: int = 2048
) -> UUID:
    """
    Import base consultation data (consultation, respondents, questions, responses) into database.

    This function is idempotent and can be safely re-run. It will update existing
    consultations rather than creating duplicates.

    Base consultation data includes:
    - Consultation definition
    - Respondents and their demographics
    - Questions and their configuration
    - Response text (both free text and multiple choice)

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

    # 2. Create respondents with demographics
    _ingest_respondents(consultation, batch.respondents)

    # 3. Create questions with multi-choice options
    _ingest_questions(consultation, batch.questions)

    # 4. Create responses (free text and multi-choice)
    _ingest_responses(
        consultation, batch.responses_by_question, batch.multi_choice_by_question, batch_size
    )

    logger.info(
        "Completed consultation data ingestion for {consultation_code}",
        consultation_code=consultation.code,
    )
    return consultation.id


def _ingest_respondents(consultation: Consultation, respondents: List[RespondentInput]) -> None:
    """
    Create respondents and their demographics for a consultation.

    This deletes existing respondents for idempotency.

    Args:
        consultation: Consultation object
        respondents: List of validated respondent inputs
    """
    logger.info("Ingesting {respondent_count} respondents", respondent_count=len(respondents))

    # Delete existing respondents for idempotency (cascades to responses)
    existing_count = Respondent.objects.filter(consultation=consultation).count()
    if existing_count > 0:
        logger.warning(
            "Deleting {existing_count} existing respondents for idempotency",
            existing_count=existing_count,
        )
        Respondent.objects.filter(consultation=consultation).delete()

    # Create respondents
    respondents_to_create = []
    for respondent_input in respondents:
        respondent = Respondent(
            consultation=consultation,
            themefinder_id=respondent_input.themefinder_id,
        )
        respondents_to_create.append((respondent, respondent_input))

    created_respondents = Respondent.objects.bulk_create([r for r, _ in respondents_to_create])

    # Create demographics for each respondent
    for respondent, (_, respondent_input) in zip(created_respondents, respondents_to_create):
        if not respondent_input.demographic_data:
            continue

        demographic_options = []
        for field_name, field_values in respondent_input.demographic_data.items():
            for field_value in field_values:
                option, _ = DemographicOption.objects.get_or_create(
                    consultation=consultation,
                    field_name=field_name,
                    field_value=field_value,
                )
                demographic_options.append(option)

        if demographic_options:
            respondent.demographics.set(demographic_options)

    logger.info("Created {respondent_count} respondents", respondent_count=len(created_respondents))


def _ingest_questions(consultation: Consultation, questions: List[QuestionInput]) -> None:
    """
    Create questions and their multi-choice options for a consultation.

    This deletes existing questions for idempotency (cascades to responses).

    Args:
        consultation: Consultation object
        questions: List of validated question inputs
    """
    logger.info("Ingesting {question_count} questions", question_count=len(questions))

    # Delete existing questions for idempotency (cascades to responses)
    existing_count = Question.objects.filter(consultation=consultation).count()
    if existing_count > 0:
        logger.warning(
            "Deleting {existing_count} existing questions for idempotency",
            existing_count=existing_count,
        )
        Question.objects.filter(consultation=consultation).delete()

    # Create questions
    questions_to_create = []
    for question_input in questions:
        has_mc = len(question_input.multi_choice_options) > 0
        question = Question(
            consultation=consultation,
            text=question_input.question_text,
            number=question_input.question_number,
            has_free_text=question_input.has_free_text,
            has_multiple_choice=has_mc,
        )
        questions_to_create.append((question, question_input))

    created_questions = Question.objects.bulk_create([q for q, _ in questions_to_create])

    # Create multi-choice options for each question
    for question, (_, question_input) in zip(created_questions, questions_to_create):
        if not question_input.multi_choice_options:
            continue

        options = [
            MultiChoiceAnswer(question=question, text=option_text)
            for option_text in question_input.multi_choice_options
        ]
        MultiChoiceAnswer.objects.bulk_create(options)

    logger.info("Created {question_count} questions", question_count=len(created_questions))


def _ingest_responses(
    consultation: Consultation,
    responses_by_question: Dict[int, List[ResponseInput]],
    multi_choice_by_question: Dict[int, List[MultiChoiceInput]],
    batch_size: int = 2048,
) -> None:
    """
    Create responses with careful indexing to link correct respondent + question.

    This is a critical function that must correctly match:
    - themefinder_id -> Respondent
    - question_number -> Question
    - Merge free text and multi-choice by themefinder_id

    Args:
        consultation: Consultation object
        responses_by_question: Dict mapping question_number to list of ResponseInputs
        multi_choice_by_question: Dict mapping question_number to list of MultiChoiceInputs
    """
    logger.info("Ingesting responses")

    # Build lookup dictionaries for efficient indexing
    respondent_lookup = {
        r.themefinder_id: r for r in Respondent.objects.filter(consultation=consultation)
    }

    question_lookup = {q.number: q for q in Question.objects.filter(consultation=consultation)}

    # Process each question
    for question_number, question in question_lookup.items():
        logger.info(
            "Processing responses for question {question_number}", question_number=question_number
        )

        free_text_responses = responses_by_question.get(question_number, [])
        multi_choice_responses = multi_choice_by_question.get(question_number, [])

        # Merge free text and multi-choice by themefinder_id
        responses_by_tf_id: Dict[int, Dict] = {}

        for resp in free_text_responses:
            responses_by_tf_id[resp.themefinder_id] = {
                "free_text": resp.text,
                "multi_choice": None,
            }

        for mc in multi_choice_responses:
            if mc.themefinder_id in responses_by_tf_id:
                responses_by_tf_id[mc.themefinder_id]["multi_choice"] = mc.options
            else:
                responses_by_tf_id[mc.themefinder_id] = {
                    "free_text": None,
                    "multi_choice": mc.options,
                }

        # Create Response objects with batching based on token count
        responses_to_create: List = []
        max_total_tokens = 100_000
        total_tokens = 0

        for i, (tf_id, data) in enumerate(responses_by_tf_id.items()):
            if tf_id not in respondent_lookup:
                logger.warning("No respondent found for themefinder_id {tf_id}", tf_id=tf_id)
                continue

            free_text = data["free_text"]

            # Calculate tokens for free text
            if free_text:
                token_count = len(encoding.encode(free_text))
                if token_count > 8192:
                    logger.warning("Truncated text for themefinder_id: {tf_id}", tf_id=tf_id)
                    free_text = free_text[:1000]
                    token_count = len(encoding.encode(free_text))
            else:
                token_count = 0

            # Batch by token count or size
            if (
                total_tokens + token_count > max_total_tokens
                or len(responses_to_create) >= batch_size
            ):
                Response.objects.bulk_create([r for r, _ in responses_to_create])
                responses_to_create = []
                total_tokens = 0
                logger.info(
                    f"Saved batch of responses for question {question_number} (total so far: {i + 1})"
                )

            response = Response(
                respondent=respondent_lookup[tf_id],
                question=question,
                free_text=free_text,
            )

            responses_to_create.append((response, data["multi_choice"]))
            total_tokens += token_count

        # Save last batch
        if responses_to_create:
            created_responses = Response.objects.bulk_create([r for r, _ in responses_to_create])

            # Set multi-choice options (requires M2M after creation)
            mc_options_lookup = {
                opt.text: opt for opt in MultiChoiceAnswer.objects.filter(question=question)
            }

            for response, (_, mc_options) in zip(created_responses, responses_to_create):
                if mc_options:
                    chosen = [
                        mc_options_lookup[text] for text in mc_options if text in mc_options_lookup
                    ]
                    if chosen:
                        response.chosen_options.set(chosen)
                        response.save()

            # Update search vectors (via signal on save)
            for response in created_responses:
                if response.free_text:
                    response.save()

            logger.info(
                f"Saved final batch of {len(created_responses)} responses for question {question_number}"
            )

        # Update question total_responses count
        question.update_total_responses()
        logger.info(
            f"Updated total_responses count for question {question_number}: {question.total_responses}"
        )

    logger.info("Completed response ingestion")


# =============================================================================
# ASYNC JOBS - Background processing
# =============================================================================


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
    enqueue_embeddings: bool = True,
    batch_size: int = 2048,
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
        queue = get_queue(default_timeout=DEFAULT_TIMEOUT_SECONDS)

        for question in Question.objects.filter(consultation=consultation):
            if question.has_free_text:
                logger.info(
                    "Enqueueing embedding job for question {question_number}",
                    question_number=question.number,
                )
                queue.enqueue(create_embeddings_for_question, question.id)

    logger.info("Completed S3 import for {consultation_code}", consultation_code=consultation_code)
    return consultation_id
