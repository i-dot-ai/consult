import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.db import transaction

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Response,
    ResponseAnnotation,
    SelectedTheme,
)
from consultation_analyser.support_console.ingestion.pydantic_models import (
    AnnotationBatch,
    DetailDetectionInput,
    SelectedThemeInput,
    SentimentInput,
    ThemeMappingInput,
)
from consultation_analyser.support_console.ingestion.s3_utils import (
    read_json_from_s3,
    read_jsonl_from_s3,
)

logger = logging.getLogger(__name__)


# ============================================================================
# S3 LOADERS - Load and validate data from S3
# ============================================================================


def load_selected_themes_from_s3(
    consultation_code: str,
    question_number: int,
    timestamp: str,
    bucket_name: Optional[str] = None,
    s3_client=None,
) -> List[SelectedThemeInput]:
    """
    Load and validate selected themes for a single question from S3.

    Args:
        consultation_code: The consultation folder name in S3
        question_number: The question number (e.g., 1 for question_part_1)
        timestamp: The timestamp folder identifying the mapping run
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)
        s3_client: Optional boto3 S3 client (for testing)

    Returns:
        List of validated SelectedThemeInput objects

    Raises:
        ValidationError: If S3 data doesn't match expected schema
    """
    bucket_name_str = bucket_name if bucket_name is not None else settings.AWS_BUCKET_NAME

    # Build S3 key for themes.json
    key = f"app_data/consultations/{consultation_code}/outputs/mapping/{timestamp}/question_part_{question_number}/themes.json"

    logger.info(f"Loading selected themes from {key}")

    # Read and parse JSON file
    try:
        theme_data = read_json_from_s3(
            bucket_name=bucket_name_str, key=key, s3_client=s3_client, raise_if_missing=True
        )
    except Exception:
        msg = f"key {key} not found"
        logger.error(msg)
        raise KeyError(msg)

    # Validate each theme using Pydantic
    # Note: theme_data is guaranteed to be non-None because raise_if_missing=True
    assert theme_data is not None  # type narrowing for mypy
    validated_themes = [SelectedThemeInput(**theme) for theme in theme_data]

    logger.info(
        f"Loaded and validated {len(validated_themes)} selected themes for question {question_number}"
    )

    return validated_themes


def load_sentiments_from_s3(
    consultation_code: str,
    question_number: int,
    timestamp: str,
    bucket_name: Optional[str] = None,
    s3_client=None,
) -> List[SentimentInput]:
    """
    Load and validate sentiments for a single question from S3.

    Note: sentiment.jsonl is optional and may not exist for all consultations.

    Args:
        consultation_code: The consultation folder name in S3
        question_number: The question number
        timestamp: The timestamp folder identifying the mapping run
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)
        s3_client: Optional boto3 S3 client (for testing)

    Returns:
        List of validated SentimentInput objects (empty if file doesn't exist)
    """
    bucket_name_str = bucket_name if bucket_name is not None else settings.AWS_BUCKET_NAME

    key = f"app_data/consultations/{consultation_code}/outputs/mapping/{timestamp}/question_part_{question_number}/sentiment.jsonl"

    logger.info(f"Loading sentiments from {key}")

    # Read JSONL file (raise_if_missing=False because sentiment is optional)
    sentiment_data = read_jsonl_from_s3(
        bucket_name=bucket_name_str, key=key, s3_client=s3_client, raise_if_missing=False
    )

    if not sentiment_data:
        logger.info(f"No sentiment file found at {key} (this is optional)")
        return []

    # Validate each sentiment using Pydantic
    validated_sentiments = [SentimentInput(**item) for item in sentiment_data]

    logger.info(
        f"Loaded and validated {len(validated_sentiments)} sentiments for question {question_number}"
    )

    return validated_sentiments


def load_detail_detections_from_s3(
    consultation_code: str,
    question_number: int,
    timestamp: str,
    bucket_name: Optional[str] = None,
    s3_client=None,
) -> List[DetailDetectionInput]:
    """
    Load and validate detail detection data for a single question from S3.

    Args:
        consultation_code: The consultation folder name in S3
        question_number: The question number
        timestamp: The timestamp folder identifying the mapping run
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)
        s3_client: Optional boto3 S3 client (for testing)

    Returns:
        List of validated DetailDetectionInput objects

    Raises:
        ValidationError: If S3 data doesn't match expected schema
    """
    bucket_name_str = bucket_name if bucket_name is not None else settings.AWS_BUCKET_NAME

    key = f"app_data/consultations/{consultation_code}/outputs/mapping/{timestamp}/question_part_{question_number}/detail_detection.jsonl"

    logger.info(f"Loading detail detections from {key}")

    # Read JSONL file
    detail_data = read_jsonl_from_s3(
        bucket_name=bucket_name_str, key=key, s3_client=s3_client, raise_if_missing=True
    )

    # Validate each item using Pydantic
    validated_details = [DetailDetectionInput(**item) for item in detail_data]

    logger.info(
        f"Loaded and validated {len(validated_details)} detail detections for question {question_number}"
    )

    return validated_details


def load_theme_mappings_from_s3(
    consultation_code: str,
    question_number: int,
    timestamp: str,
    bucket_name: Optional[str] = None,
    s3_client=None,
) -> List[ThemeMappingInput]:
    """
    Load and validate theme mappings for a single question from S3.

    Args:
        consultation_code: The consultation folder name in S3
        question_number: The question number
        timestamp: The timestamp folder identifying the mapping run
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)
        s3_client: Optional boto3 S3 client (for testing)

    Returns:
        List of validated ThemeMappingInput objects

    Raises:
        ValidationError: If S3 data doesn't match expected schema
    """
    bucket_name_str = bucket_name if bucket_name is not None else settings.AWS_BUCKET_NAME

    key = f"app_data/consultations/{consultation_code}/outputs/mapping/{timestamp}/question_part_{question_number}/mapping.jsonl"

    logger.info(f"Loading theme mappings from {key}")

    # Read JSONL file
    mapping_data = read_jsonl_from_s3(
        bucket_name=bucket_name_str, key=key, s3_client=s3_client, raise_if_missing=True
    )

    # Validate each mapping using Pydantic
    validated_mappings = [ThemeMappingInput(**item) for item in mapping_data]

    logger.info(
        f"Loaded and validated {len(validated_mappings)} theme mappings for question {question_number}"
    )

    return validated_mappings


def load_annotation_batch(
    consultation_code: str,
    timestamp: str,
    question_numbers: Optional[List[int]] = None,
    bucket_name: Optional[str] = None,
    s3_client=None,
) -> AnnotationBatch:
    """
    Load all response annotations for a consultation, organized by question.

    Args:
        consultation_code: The consultation folder name in S3
        timestamp: The timestamp folder identifying the mapping run
        question_numbers: Optional list of question numbers to load (defaults to all questions in consultation)
        bucket_name: S3 bucket name (defaults to settings.AWS_BUCKET_NAME)
        s3_client: Optional boto3 S3 client (for testing)

    Returns:
        AnnotationBatch with all annotations organized by question number

    Raises:
        ValidationError: If S3 data doesn't match expected schema
        ValueError: If consultation doesn't exist
    """
    bucket_name_str = bucket_name if bucket_name is not None else settings.AWS_BUCKET_NAME

    # If question_numbers not provided, get questions that have responses
    if question_numbers is None:
        try:
            consultation = Consultation.objects.get(code=consultation_code)
            question_numbers = list(
                Question.objects.filter(
                    consultation=consultation,
                    has_free_text=True,
                    response__free_text__isnull=False,
                )
                .exclude(response__free_text="")
                .distinct()
                .values_list("number", flat=True)
            )
        except Consultation.DoesNotExist:
            raise ValueError(
                f"Consultation with code '{consultation_code}' does not exist. "
                "Immutable data must be imported before annotations."
            )

    logger.info(
        f"Loading annotations for consultation '{consultation_code}' "
        f"(timestamp: {timestamp}) across {len(question_numbers)} questions"
    )

    # Load data for each question
    sentiments_by_question: Dict[int, List[SentimentInput]] = {}
    details_by_question: Dict[int, List[DetailDetectionInput]] = {}
    mappings_by_question: Dict[int, List[ThemeMappingInput]] = {}
    selected_themes_by_question: Dict[int, List[SelectedThemeInput]] = {}

    for question_number in question_numbers:
        # Load selected themes (required)
        themes = load_selected_themes_from_s3(
            consultation_code, question_number, timestamp, bucket_name_str, s3_client
        )
        selected_themes_by_question[question_number] = themes

        # Load sentiments (optional)
        sentiments = load_sentiments_from_s3(
            consultation_code, question_number, timestamp, bucket_name_str, s3_client
        )
        if sentiments:
            sentiments_by_question[question_number] = sentiments

        # Load detail detections (required)
        details = load_detail_detections_from_s3(
            consultation_code, question_number, timestamp, bucket_name_str, s3_client
        )
        details_by_question[question_number] = details

        # Load theme mappings (required)
        mappings = load_theme_mappings_from_s3(
            consultation_code, question_number, timestamp, bucket_name_str, s3_client
        )
        mappings_by_question[question_number] = mappings

    # Create batch object
    batch = AnnotationBatch(
        consultation_code=consultation_code,
        timestamp=timestamp,
        sentiments_by_question=sentiments_by_question,
        details_by_question=details_by_question,
        mappings_by_question=mappings_by_question,
        selected_themes_by_question=selected_themes_by_question,
    )

    total_sentiments = sum(len(s) for s in sentiments_by_question.values())
    total_details = sum(len(d) for d in details_by_question.values())
    total_mappings = sum(len(m) for m in mappings_by_question.values())
    total_themes = sum(len(t) for t in selected_themes_by_question.values())

    logger.info(
        f"Loaded annotation batch: {total_themes} themes, {total_sentiments} sentiments, "
        f"{total_details} detail detections, {total_mappings} mappings across {len(question_numbers)} questions"
    )

    return batch


# ============================================================================
# INGESTION LOGIC - Create Django models from validated data
# ============================================================================


def _ingest_selected_themes(
    question: Question, themes: List[SelectedThemeInput]
) -> Dict[str, SelectedTheme]:
    """
    Ingest selected themes for a single question.

    This function is idempotent - deletes existing selected themes before creating new ones.

    Args:
        question: The Question instance to attach themes to
        themes: List of validated SelectedThemeInput objects

    Returns:
        Dictionary mapping theme_key -> SelectedTheme instance (for linking annotations)
    """
    if not themes:
        logger.info(f"No selected themes to ingest for question {question.number}")
        return {}

    # Delete existing selected themes for this question (idempotent)
    existing_count = SelectedTheme.objects.filter(question=question).count()
    if existing_count > 0:
        logger.info(
            f"Deleting {existing_count} existing selected themes for question {question.number}"
        )
        SelectedTheme.objects.filter(question=question).delete()

    logger.info(f"Ingesting {len(themes)} selected themes for question {question.number}")

    # Create all themes
    themes_to_create = [
        SelectedTheme(
            question=question,
            key=theme.theme_key,
            name=theme.theme_name,
            description=theme.theme_description,
        )
        for theme in themes
    ]

    created_themes = SelectedTheme.objects.bulk_create(themes_to_create)

    # Build mapping from theme_key to SelectedTheme for later use
    theme_lookup = {theme.key: theme for theme in created_themes}

    logger.info(f"Created {len(created_themes)} selected themes for question {question.number}")

    return theme_lookup


def _ingest_response_annotations(
    question: Question,
    sentiments: List[SentimentInput],
    details: List[DetailDetectionInput],
    mappings: List[ThemeMappingInput],
    theme_lookup: Dict[str, SelectedTheme],
) -> None:
    """
    Ingest response annotations for a single question.

    Creates ResponseAnnotation objects with sentiment and evidence_rich data,
    then links them to themes via ResponseAnnotationTheme.

    This function is idempotent - deletes existing annotations before creating new ones.

    Args:
        question: The Question instance
        sentiments: List of sentiment inputs (may be empty)
        details: List of detail detection inputs
        mappings: List of theme mapping inputs
        theme_lookup: Dictionary mapping theme_key -> SelectedTheme
    """
    # Delete existing annotations for this question (idempotent)
    existing_count = ResponseAnnotation.objects.filter(response__question=question).count()
    if existing_count > 0:
        logger.info(
            f"Deleting {existing_count} existing annotations for question {question.number}"
        )
        ResponseAnnotation.objects.filter(response__question=question).delete()

    logger.info(f"Ingesting annotations for question {question.number}")

    # Build lookups for efficient matching
    sentiment_lookup = {s.themefinder_id: s.sentiment for s in sentiments}
    detail_lookup = {d.themefinder_id: d.as_bool for d in details}
    mapping_lookup = {m.themefinder_id: m.theme_keys for m in mappings}

    # Get all responses for this question with their respondent themefinder_ids
    responses = Response.objects.filter(question=question).select_related("respondent")
    response_lookup = {r.respondent.themefinder_id: r for r in responses}

    # Create ResponseAnnotation objects
    annotations_to_create = []
    annotation_theme_data = []  # Store (themefinder_id, theme_keys) for later

    for themefinder_id, response in response_lookup.items():
        # Get sentiment (default to UNCLEAR if not present)
        sentiment = sentiment_lookup.get(themefinder_id, "UNCLEAR")

        # Get evidence_rich (default to False if not present)
        evidence_rich = detail_lookup.get(themefinder_id, False)

        # Create annotation
        annotation = ResponseAnnotation(
            response=response,
            sentiment=sentiment,
            evidence_rich=evidence_rich,
            human_reviewed=False,  # AI-generated, not human-reviewed
        )
        annotations_to_create.append(annotation)

        # Store theme mappings for this response
        theme_keys = mapping_lookup.get(themefinder_id, [])
        if theme_keys:
            annotation_theme_data.append((themefinder_id, theme_keys))

    # Bulk create annotations
    created_annotations = ResponseAnnotation.objects.bulk_create(annotations_to_create)

    logger.info(
        f"Created {len(created_annotations)} response annotations for question {question.number}"
    )

    # Now link annotations to themes
    # Rebuild lookup with created annotation objects
    annotation_by_tf_id = {}
    for annotation in created_annotations:
        tf_id = annotation.response.respondent.themefinder_id
        annotation_by_tf_id[tf_id] = annotation

    # Create ResponseAnnotationTheme links using add_original_ai_themes
    themes_linked = 0
    for themefinder_id, theme_keys in annotation_theme_data:
        annotation = annotation_by_tf_id[themefinder_id]

        # Get SelectedTheme objects for these keys
        themes_to_link = []
        for theme_key in theme_keys:
            if theme_key in theme_lookup:
                themes_to_link.append(theme_lookup[theme_key])
            else:
                logger.warning(
                    f"Theme key '{theme_key}' not found in selected themes for question {question.number}"
                )

        # Link themes to annotation (as AI-assigned themes)
        if themes_to_link:
            annotation.add_original_ai_themes(themes_to_link)
            themes_linked += len(themes_to_link)

    logger.info(f"Linked {themes_linked} theme assignments for question {question.number}")


@transaction.atomic
def ingest_response_annotations(batch: AnnotationBatch) -> None:
    """
    Ingest all response annotations from a batch into the database.

    This is the main ingestion function that:
    1. Validates that the consultation exists
    2. Updates the consultation's timestamp
    3. For each question:
       a. Ingests selected themes
       b. Ingests response annotations (sentiment, evidence, theme mappings)

    This function is idempotent - can safely re-run to update annotations.

    Args:
        batch: AnnotationBatch containing all annotations to ingest

    Raises:
        ValueError: If consultation doesn't exist or questions are missing
    """
    # Get consultation
    try:
        consultation = Consultation.objects.get(code=batch.consultation_code)
    except Consultation.DoesNotExist:
        raise ValueError(
            f"Consultation with code '{batch.consultation_code}' does not exist. "
            "Immutable data must be imported before annotations."
        )

    logger.info(f"Starting annotation ingestion for consultation '{consultation.title}'")

    # Update consultation timestamp
    if consultation.timestamp != batch.timestamp:
        logger.info(
            f"Updating consultation timestamp from '{consultation.timestamp}' to '{batch.timestamp}'"
        )
        consultation.timestamp = batch.timestamp
        consultation.save(update_fields=["timestamp"])

    # Ingest data for each question
    questions_processed = 0

    for question_number in batch.selected_themes_by_question.keys():
        # Get question
        try:
            question = Question.objects.get(consultation=consultation, number=question_number)
        except Question.DoesNotExist:
            raise ValueError(
                f"Question {question_number} does not exist for consultation '{batch.consultation_code}'. "
                "Immutable data must be imported before annotations."
            )

        # Ingest selected themes first (needed for theme lookups)
        themes_for_question = batch.selected_themes_by_question[question_number]
        theme_lookup = _ingest_selected_themes(question, themes_for_question)

        # Ingest response annotations
        sentiments = batch.sentiments_by_question.get(question_number, [])
        details = batch.details_by_question.get(question_number, [])
        mappings = batch.mappings_by_question.get(question_number, [])

        _ingest_response_annotations(question, sentiments, details, mappings, theme_lookup)

        questions_processed += 1

    logger.info(f"Annotation ingestion complete for {questions_processed} questions")


# ============================================================================
# ORCHESTRATION - High-level functions to coordinate the workflow
# ============================================================================


def import_response_annotations_from_s3(
    consultation_code: str,
    timestamp: str,
    question_numbers: Optional[List[int]] = None,
) -> None:
    """
    High-level orchestration function to import response annotations from S3.

    This function:
    1. Loads response annotations from S3 for all questions
    2. Validates data using Pydantic models
    3. Ingests annotations into the database

    Args:
        consultation_code: The consultation folder name in S3
        timestamp: The timestamp folder identifying the mapping run
        question_numbers: Optional list of question numbers to import (defaults to all)

    Raises:
        ValidationError: If S3 data doesn't match expected schema
        ValueError: If consultation or questions don't exist
    """
    logger.info(
        f"Starting response annotations import for consultation '{consultation_code}' "
        f"(timestamp: {timestamp})"
    )

    # Load from S3
    batch = load_annotation_batch(
        consultation_code=consultation_code,
        timestamp=timestamp,
        question_numbers=question_numbers,
    )

    # Ingest into database
    ingest_response_annotations(batch)

    logger.info(f"Response annotations import complete for consultation '{consultation_code}'")
