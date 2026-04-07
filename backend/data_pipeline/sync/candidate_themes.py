import csv
import io
from typing import Dict, List, Optional

import boto3
from django.conf import settings
from django.db import transaction
from themefinder.models import ThemeNode

import data_pipeline.s3 as s3
from consultations.models import (
    CandidateTheme,
    CandidateThemeResponse,
    Consultation,
    Question,
    Response,
)
from data_pipeline.models import CandidateThemeBatch, ThemeMappingInput, ThemeNodeList

logger = settings.LOGGER


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

    logger.info("Loading candidate themes from {key}", key=key)

    # Read and parse JSON file
    theme_data = s3.read_json(
        bucket_name=bucket_name_str, key=key, s3_client=s3_client, raise_if_missing=False
    )

    if theme_data is None:
        logger.info("No candidate themes file found at {key}", key=key)
        return []

    validated_themes = ThemeNodeList.model_validate(theme_data).theme_nodes

    logger.info(
        "Loaded and validated {theme_count} candidate themes for question {question_number}",
        theme_count=len(validated_themes),
        question_number=question_number,
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
        "Loading candidate themes for consultation '{consultation_code}' (timestamp: {timestamp}) across {question_count} questions",
        consultation_code=consultation_code,
        timestamp=timestamp,
        question_count=len(question_numbers),
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
        "Loaded {total_themes} total candidate themes across {question_count} questions",
        total_themes=total_themes,
        question_count=len(themes_by_question),
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
        logger.info(
            "No candidate themes to import for question {question_number}",
            question_number=question.number,
        )
        return

    # Delete existing candidate themes for this question (idempotent)
    existing_count = CandidateTheme.objects.filter(question=question).count()
    if existing_count > 0:
        logger.info(
            "Deleting {existing_count} existing candidate themes for question {question_number}",
            existing_count=existing_count,
            question_number=question.number,
        )
        CandidateTheme.objects.filter(question=question).delete()

    logger.info(
        "Importing {theme_count} candidate themes for question {question_number}",
        theme_count=len(themes),
        question_number=question.number,
    )

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
                "Parent theme with topic_id '{parent_id}' not found for theme '{theme_name}'",
                parent_id=parent_id,
                theme_name=candidate_theme.name,
            )

    # Bulk update parent relationships
    if themes_to_update:
        CandidateTheme.objects.bulk_update(themes_to_update, ["parent"])
        logger.info(
            "Set {relationship_count} parent relationships",
            relationship_count=len(themes_to_update),
        )

    logger.info(
        "Created {theme_count} candidate themes for question {question_number}",
        theme_count=len(created_themes),
        question_number=question.number,
    )


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

    logger.info(
        "Starting candidate themes import for consultation '{consultation_title}'",
        consultation_title=consultation.title,
    )

    # Update consultation timestamp
    if consultation.timestamp != batch.timestamp:
        logger.info(
            "Updating consultation timestamp from '{old_timestamp}' to '{new_timestamp}'",
            old_timestamp=consultation.timestamp,
            new_timestamp=batch.timestamp,
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
        "Candidate themes import complete: {total_themes_created} themes across {questions_imported} questions",
        total_themes_created=total_themes_created,
        questions_imported=questions_imported,
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
        "Starting candidate themes import for consultation '{consultation_code}' (timestamp: {timestamp})",
        consultation_code=consultation_code,
        timestamp=timestamp,
    )

    # Load from S3
    batch = load_candidate_themes_batch(
        consultation_code=consultation_code,
        timestamp=timestamp,
        question_numbers=question_numbers,
    )

    # Import into database
    import_candidate_themes(batch)

    logger.info(
        "Candidate themes import complete for consultation '{consultation_code}'",
        consultation_code=consultation_code,
    )


# ============================================================================
# EXPORT - Export candidate themes to S3 for the assign-themes batch job
# ============================================================================


def export_candidate_themes_to_s3(consultation: Consultation) -> int:
    """
    Export all candidate themes for a consultation to S3.

    This prepares for the 'assign-themes' batch job during the finalising themes
    phase, using the same S3 format as selected themes export so the batch job
    can process them identically.

    Args:
        consultation: The consultation whose candidate themes should be exported

    Returns:
        Number of questions that had themes exported

    Raises:
        ValueError: If no questions have candidate themes
    """
    s3_client = boto3.client("s3")
    questions_exported = 0

    questions = consultation.question_set.filter(has_free_text=True)

    for question in questions:
        # Only export top-level candidate themes (not children)
        themes = CandidateTheme.objects.filter(question=question, parent__isnull=True)

        if not themes.exists():
            logger.warning(
                "No candidate themes found for question {question_number} "
                "in consultation {consultation_title}",
                question_number=question.number,
                consultation_title=consultation.title,
            )
            continue

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Theme Name", "Theme Description"])

        for theme in themes:
            writer.writerow([theme.name, theme.description])

        s3_path = (
            f"app_data/consultations/{consultation.code}/inputs/"
            f"question_part_{question.number}/themes.csv"
        )
        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME, Key=s3_path, Body=csv_buffer.getvalue()
        )

        logger.info(
            "Exported {themes_count} candidate themes for question {question_number} to {s3_path}",
            themes_count=themes.count(),
            question_number=question.number,
            s3_path=s3_path,
        )
        questions_exported += 1

    if questions_exported == 0:
        raise ValueError(
            f"No questions with candidate themes found for consultation '{consultation.title}'"
        )

    logger.info(
        "Exported candidate themes for {questions_exported} questions in consultation '{consultation_title}'",
        questions_exported=questions_exported,
        consultation_title=consultation.title,
    )

    return questions_exported


# ============================================================================
# IMPORT CANDIDATE THEME RESPONSES - Import batch job mapping results
# ============================================================================


def _build_candidate_theme_lookup(
    question: Question,
    batch_themes: List,
) -> Dict[str, CandidateTheme]:
    """
    Build a lookup from batch job theme_keys to database CandidateTheme records.

    Matches on theme NAME (the stable identifier across both systems),
    mirroring the approach used for SelectedTheme in response_annotations.py.
    """
    if not batch_themes:
        return {}

    db_themes = CandidateTheme.objects.filter(question=question, parent__isnull=True)
    db_themes_by_name = {theme.name: theme for theme in db_themes}

    batch_key_to_db_theme = {}
    missing_themes = []

    for batch_theme in batch_themes:
        if batch_theme.theme_name in db_themes_by_name:
            batch_key_to_db_theme[batch_theme.theme_key] = db_themes_by_name[batch_theme.theme_name]
        else:
            missing_themes.append(batch_theme.theme_name)
            logger.warning(
                "Theme '{theme_name}' from batch output not found in candidate themes for question {question_number}",
                theme_name=batch_theme.theme_name,
                question_number=question.number,
            )

    if missing_themes:
        raise ValueError(
            f"Batch output contains themes not found in candidate themes for question {question.number}: "
            f"{missing_themes}."
        )

    return batch_key_to_db_theme


def _import_candidate_theme_responses(
    question: Question,
    mappings: List[ThemeMappingInput],
    theme_lookup: Dict[str, CandidateTheme],
) -> None:
    """
    Import candidate theme to response mappings for a single question.

    Deletes existing CandidateThemeResponse records for this question's themes
    before creating new ones (idempotent).
    """
    # Delete existing mappings for this question's candidate themes
    CandidateThemeResponse.objects.filter(candidate_theme__question=question).delete()

    # Build response lookup by themefinder_id
    responses = Response.objects.filter(question=question).select_related("respondent")
    response_lookup = {r.respondent.themefinder_id: r for r in responses}

    mapping_lookup = {m.themefinder_id: m.theme_keys for m in mappings}

    records_to_create = []

    for themefinder_id, response in response_lookup.items():
        theme_keys = mapping_lookup.get(themefinder_id, [])
        for theme_key in theme_keys:
            if theme_key in theme_lookup:
                records_to_create.append(
                    CandidateThemeResponse(
                        candidate_theme=theme_lookup[theme_key],
                        response=response,
                    )
                )

    if records_to_create:
        CandidateThemeResponse.objects.bulk_create(records_to_create, ignore_conflicts=True)

    logger.info(
        "Created {count} candidate theme response links for question {question_number}",
        count=len(records_to_create),
        question_number=question.number,
    )


@transaction.atomic
def import_candidate_theme_responses(
    consultation_code: str,
    timestamp: str,
) -> None:
    """
    Import candidate theme response mappings from S3 batch job output.

    Reads the same mapping.jsonl and themes.json output as the normal
    assign-themes import, but populates CandidateThemeResponse instead
    of ResponseAnnotation.
    """
    from data_pipeline.sync.response_annotations import (
        load_selected_themes_from_s3,
        load_theme_mappings_from_s3,
    )

    try:
        consultation = Consultation.objects.get(code=consultation_code)
    except Consultation.DoesNotExist:
        raise ValueError(f"Consultation with code '{consultation_code}' does not exist.")

    logger.info(
        "Starting candidate theme response import for consultation '{consultation_title}'",
        consultation_title=consultation.title,
    )

    questions = consultation.question_set.filter(has_free_text=True)

    for question in questions:
        # Load themes.json (same format as selected themes output)
        batch_themes = load_selected_themes_from_s3(
            consultation_code=consultation_code,
            question_number=question.number,
            timestamp=timestamp,
        )

        # Load mapping.jsonl
        mappings = load_theme_mappings_from_s3(
            consultation_code=consultation_code,
            question_number=question.number,
            timestamp=timestamp,
        )

        # Build lookup from batch theme_key -> CandidateTheme
        theme_lookup = _build_candidate_theme_lookup(question, batch_themes)

        # Import mappings
        _import_candidate_theme_responses(question, mappings, theme_lookup)

    logger.info(
        "Candidate theme response import complete for consultation '{consultation_title}'",
        consultation_title=consultation.title,
    )


def import_candidate_theme_responses_from_s3(
    consultation_code: str,
    timestamp: str,
) -> None:
    """
    High-level orchestration function to import candidate theme responses from S3.
    """
    logger.info(
        "Starting candidate theme response import for '{consultation_code}' (timestamp: {timestamp})",
        consultation_code=consultation_code,
        timestamp=timestamp,
    )

    import_candidate_theme_responses(
        consultation_code=consultation_code,
        timestamp=timestamp,
    )

    logger.info(
        "Candidate theme response import complete for '{consultation_code}'",
        consultation_code=consultation_code,
    )
