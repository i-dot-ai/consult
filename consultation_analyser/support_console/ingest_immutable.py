from typing import Dict, List, Optional

import boto3
import tiktoken
from django.conf import settings

from consultation_analyser.support_console.pydantic_models import (
    ImmutableDataBatch,
    MultiChoiceInput,
    QuestionInput,
    RespondentInput,
    ResponseInput,
)
from consultation_analyser.support_console.s3_utils import (
    get_question_folders,
    read_json_from_s3,
    read_jsonl_from_s3,
)

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

    logger.info(f"Loading respondents from {key}")

    raw_data = read_jsonl_from_s3(bucket_name, key, s3_client)

    respondents = [RespondentInput(**data) for data in raw_data]

    logger.info(f"Loaded and validated {len(respondents)} respondents")
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

    logger.info(f"Loading question {question_number} from {key}")

    data = read_json_from_s3(bucket_name, key, s3_client)

    if data is None:
        raise ValueError(f"Question file not found or empty: {key}")

    # Ensure question_number is set (might not be in the file)
    data["question_number"] = question_number

    question = QuestionInput(**data)

    logger.info(f"Loaded and validated question {question_number}")
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

    logger.info(f"Loading responses for question {question_number} from {key}")

    raw_data = read_jsonl_from_s3(bucket_name, key, s3_client, raise_if_missing=False)

    responses = []
    for data in raw_data:
        # Only include responses that have text
        if data.get("text"):
            responses.append(ResponseInput(**data))

    logger.info(f"Loaded and validated {len(responses)} responses for question {question_number}")
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

    logger.info(f"Loading multi-choice data for question {question_number} from {key}")

    raw_data = read_jsonl_from_s3(bucket_name, key, s3_client, raise_if_missing=False)

    multi_choices = []
    for data in raw_data:
        # Only include if they have options selected
        if data.get("options"):
            multi_choices.append(MultiChoiceInput(**data))

    logger.info(
        f"Loaded and validated {len(multi_choices)} multi-choice responses for question {question_number}"
    )
    return multi_choices


def load_immutable_data_batch(
    consultation_code: str,
    consultation_title: str,
    timestamp: Optional[str] = None,
    bucket_name: Optional[str] = None,
) -> ImmutableDataBatch:
    """
    Load and validate all immutable consultation data from S3.

    This orchestrates loading:
    - Respondents
    - Questions
    - Free text responses
    - Multi-choice selections

    Args:
        consultation_code: Consultation code (S3 folder name)
        consultation_title: Display title for the consultation
        timestamp: Optional timestamp for outputs
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)

    Returns:
        Validated ImmutableDataBatch with all data
    """
    if bucket_name is None:
        bucket_name = settings.AWS_BUCKET_NAME

    logger.info(f"Loading immutable data batch for consultation {consultation_code}")

    s3_client = boto3.client("s3")

    # Load respondents
    respondents = load_respondents_from_s3(consultation_code, bucket_name, s3_client)

    # Discover question folders
    inputs_path = f"app_data/consultations/{consultation_code}/inputs/"
    question_folders = get_question_folders(inputs_path, bucket_name)

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
    batch = ImmutableDataBatch(
        consultation_code=consultation_code,
        consultation_title=consultation_title,
        timestamp=timestamp,
        respondents=respondents,
        questions=questions,
        responses_by_question=responses_by_question,
        multi_choice_by_question=multi_choice_by_question,
    )

    logger.info(
        f"Loaded immutable data batch: {len(respondents)} respondents, "
        f"{len(questions)} questions, "
        f"{sum(len(r) for r in responses_by_question.values())} total responses"
    )

    return batch
