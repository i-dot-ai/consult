import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.db import transaction
from themefinder.models import ThemeNode

import backend.data_pipeline.s3 as s3
from backend.consultations.models import CandidateTheme, Consultation, Question
from backend.data_pipeline.models import CandidateThemeBatch, ThemeNodeList

logger = logging.getLogger(__name__)


# ============================================================================
# S3 LOADERS - Load and validate data from S3
# ============================================================================


def load_candidate_themes_from_s3(
    consultation_code: str,
    question_number: int,
    timestamp: str,
    bucket_name: Optional[str] = None,
    s3_client=None,
) -> List[ThemeNode]:
    """
    Load and validate candidate themes for a single question from S3.

    Args:
        consultation_code: The consultation folder name in S3
        question_number: The question number (e.g., 1 for question_part_1)
        timestamp: The timestamp folder identifying the themefinder run
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)
        s3_client: Optional boto3 S3 client (for testing)

    Returns:
        List of validated CandidateThemeInput objects

    Raises:
        ValidationError: If S3 data doesn't match expected schema
        FileNotFoundError: If S3 file doesn't exist
    """
    bucket_name_str = bucket_name if bucket_name is not None else settings.AWS_BUCKET_NAME

    # Build S3 key for clustered_themes.json
    key = f"app_data/consultations/{consultation_code}/outputs/sign_off/{timestamp}/question_part_{question_number}/clustered_themes.json"

    logger.info(f"Loading candidate themes from {key}")

    # Read and parse JSON file
    theme_data = s3.read_json(
        bucket_name=bucket_name_str, key=key, s3_client=s3_client, raise_if_missing=False
    )

    if theme_data is None:
        logger.info(f"No candidate themes file found at {key}")
        return []

    validated_themes = ThemeNodeList.model_validate(theme_data).theme_nodes

    logger.info(
        f"Loaded and validated {len(validated_themes)} candidate themes for question {question_number}"
    )

    return validated_themes


def load_candidate_themes_batch(
    consultation_code: str,
    timestamp: str,
    question_numbers: Optional[List[int]] = None,
    bucket_name: Optional[str] = None,
    s3_client=None,
) -> CandidateThemeBatch:
    """
    Load all candidate themes for a consultation, organized by question.

    Args:
        consultation_code: The consultation folder name in S3
        timestamp: The timestamp folder identifying the themefinder run
        question_numbers: Optional list of question numbers to load (defaults to all questions in consultation)
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)
        s3_client: Optional boto3 S3 client (for testing)

    Returns:
        CandidateThemeBatch with all themes organized by question number

    Raises:
        ValidationError: If S3 data doesn't match expected schema
        ValueError: If consultation doesn't exist
    """
    bucket_name_str = bucket_name if bucket_name is not None else settings.AWS_BUCKET_NAME

    # If question_numbers not provided, get all questions from the consultation
    if question_numbers is None:
        try:
            consultation = Consultation.objects.get(code=consultation_code)
            question_numbers = list(
                Question.objects.filter(consultation=consultation).values_list("number", flat=True)
            )
        except Consultation.DoesNotExist:
            raise ValueError(
                f"Consultation with code '{consultation_code}' does not exist. "
                "Base consultation data must be imported before candidate themes."
            )

    logger.info(
        f"Loading candidate themes for consultation '{consultation_code}' "
        f"(timestamp: {timestamp}) across {len(question_numbers)} questions"
    )

    # Load themes for each question
    themes_by_question: Dict[int, List[ThemeNode]] = {}

    for question_number in question_numbers:
        themes = load_candidate_themes_from_s3(
            consultation_code=consultation_code,
            question_number=question_number,
            timestamp=timestamp,
            bucket_name=bucket_name_str,
            s3_client=s3_client,
        )
        if themes:  # Only add if themes exist for this question
            themes_by_question[question_number] = themes

    # Create batch object
    batch = CandidateThemeBatch(
        consultation_code=consultation_code,
        timestamp=timestamp,
        themes_by_question=themes_by_question,
    )

    total_themes = sum(len(themes) for themes in themes_by_question.values())
    logger.info(
        f"Loaded {total_themes} total candidate themes across {len(themes_by_question)} questions"
    )

    return batch


# ============================================================================
# IMPORT LOGIC - Create Django models from validated data
# ============================================================================


def _import_candidate_themes_for_question(question: Question, themes: List[ThemeNode]) -> None:
    """
    Import candidate themes for a single question into database.

    Uses a two-pass approach to handle parent-child relationships:
    1. Create all themes without parent links
    2. Update parent relationships using topic_id mapping

    This function is idempotent - deletes existing candidate themes before creating new ones.

    Args:
        question: The Question instance to attach themes to
        themes: List of validated ThemeNode objects
    """
    if not themes:
        logger.info(f"No candidate themes to import for question {question.number}")
        return

    # Delete existing candidate themes for this question (idempotent)
    existing_count = CandidateTheme.objects.filter(question=question).count()
    if existing_count > 0:
        logger.info(
            f"Deleting {existing_count} existing candidate themes for question {question.number}"
        )
        CandidateTheme.objects.filter(question=question).delete()

    logger.info(f"Importing {len(themes)} candidate themes for question {question.number}")

    # First pass: create all themes without parent relationships
    themes_to_create = [
        CandidateTheme(
            question=question,
            name=theme.topic_label,
            description=theme.topic_description,
            approximate_frequency=theme.source_topic_count,
            parent=None,  # Set in second pass
        )
        for theme in themes
    ]

    created_themes = CandidateTheme.objects.bulk_create(themes_to_create)

    # Build mapping from topic_id to created CandidateTheme
    topic_id_to_candidate_theme = {}
    for theme_input, created_theme in zip(themes, created_themes):
        topic_id_to_candidate_theme[theme_input.topic_id] = created_theme

    # Second pass: set parent relationships
    themes_to_update = []
    for theme_input in themes:
        parent_id = theme_input.parent_id

        # Skip if no parent (parent_id is "0" or empty)
        if not parent_id or parent_id == "0":
            continue

        # Get the created theme for this topic_id
        candidate_theme = topic_id_to_candidate_theme[theme_input.topic_id]

        # Set parent if it exists in the mapping
        if parent_id in topic_id_to_candidate_theme:
            candidate_theme.parent = topic_id_to_candidate_theme[parent_id]
            themes_to_update.append(candidate_theme)
        else:
            logger.warning(
                f"Parent theme with topic_id '{parent_id}' not found for theme '{candidate_theme.name}'"
            )

    # Bulk update parent relationships
    if themes_to_update:
        CandidateTheme.objects.bulk_update(themes_to_update, ["parent"])
        logger.info(f"Set {len(themes_to_update)} parent relationships")

    logger.info(f"Created {len(created_themes)} candidate themes for question {question.number}")


@transaction.atomic
def import_candidate_themes(batch: CandidateThemeBatch) -> None:
    """
    Import all candidate themes from a batch into the database.

    This is the main import function that:
    1. Validates that the consultation exists
    2. Updates the consultation's timestamp
    3. Imports candidate themes for each question

    This function is idempotent - can safely re-run to update themes.

    Args:
        batch: CandidateThemeBatch containing all themes to import

    Raises:
        ValueError: If consultation doesn't exist or questions are missing
    """
    # Get consultation
    try:
        consultation = Consultation.objects.get(code=batch.consultation_code)
    except Consultation.DoesNotExist:
        raise ValueError(
            f"Consultation with code '{batch.consultation_code}' does not exist. "
            "Base consultation data must be imported before candidate themes."
        )

    logger.info(f"Starting candidate themes import for consultation '{consultation.title}'")

    # Update consultation timestamp
    if consultation.timestamp != batch.timestamp:
        logger.info(
            f"Updating consultation timestamp from '{consultation.timestamp}' to '{batch.timestamp}'"
        )
        consultation.timestamp = batch.timestamp
        consultation.save(update_fields=["timestamp"])

    # Import themes for each question
    questions_imported = 0
    total_themes_created = 0

    for question_number, themes in batch.themes_by_question.items():
        # Get question
        try:
            question = Question.objects.get(consultation=consultation, number=question_number)
        except Question.DoesNotExist:
            raise ValueError(
                f"Question {question_number} does not exist for consultation '{batch.consultation_code}'. "
                "Base consultation data must be imported before candidate themes."
            )

        # Import themes for this question
        _import_candidate_themes_for_question(question, themes)

        questions_imported += 1
        total_themes_created += len(themes)

    logger.info(
        f"Candidate themes import complete: "
        f"{total_themes_created} themes across {questions_imported} questions"
    )


# ============================================================================
# ORCHESTRATION - High-level functions to coordinate the workflow
# ============================================================================


def import_candidate_themes_from_s3(
    consultation_code: str,
    timestamp: str,
    question_numbers: Optional[List[int]] = None,
) -> None:
    """
    High-level orchestration function to import candidate themes from S3.

    This function:
    1. Loads candidate themes from S3 for all questions
    2. Validates data using Pydantic models
    3. Ingests themes into the database

    Args:
        consultation_code: The consultation folder name in S3
        timestamp: The timestamp folder identifying the themefinder run
        question_numbers: Optional list of question numbers to import (defaults to all)

    Raises:
        ValidationError: If S3 data doesn't match expected schema
        ValueError: If consultation or questions don't exist
    """
    logger.info(
        f"Starting candidate themes import for consultation '{consultation_code}' "
        f"(timestamp: {timestamp})"
    )

    # Load from S3
    batch = load_candidate_themes_batch(
        consultation_code=consultation_code,
        timestamp=timestamp,
        question_numbers=question_numbers,
    )

    # Import into database
    import_candidate_themes(batch)

    logger.info(f"Candidate themes import complete for consultation '{consultation_code}'")
