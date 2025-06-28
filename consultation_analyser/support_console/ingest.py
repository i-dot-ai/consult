import json
import logging
from uuid import UUID

import boto3
from django.conf import settings

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    Theme,
)

logger = logging.getLogger("import")
DEFAULT_BATCH_SIZE = 10000
bucket_name = settings.AWS_BUCKET_NAME


def get_question_folders(inputs_path: str, bucket_name: str) -> list[str]:
    """
    Get all question_part_N folders from the inputs path.

    Returns:
        List of folder paths ending with /
    """
    s3 = boto3.resource("s3")
    objects = s3.Bucket(bucket_name).objects.filter(Prefix=inputs_path)
    object_names_set = {obj.key for obj in objects}

    # Get set of all subfolders
    subfolders = set()
    for path in object_names_set:
        folder = "/".join(path.split("/")[:-1]) + "/"
        subfolders.add(folder)

    # Only the ones that are question_folders
    question_folders = [
        "/".join(name.split("/")[:-1]) + "/"
        for name in subfolders
        if name.split("/")[-2].startswith("question_part_")
    ]
    question_folders.sort()
    return question_folders


def get_consultation_codes() -> list[dict]:
    """
    Get all available consultation codes from S3 for dropdown selection.

    Returns:
        List of dicts with 'text' and 'value' keys for form dropdown
    """
    try:
        s3 = boto3.resource("s3")
        objects = s3.Bucket(settings.AWS_BUCKET_NAME).objects.filter(Prefix="app_data/")

        # Get unique consultation folders
        consultation_codes = set()
        for obj in objects:
            parts = obj.key.split("/")
            if len(parts) >= 2 and parts[1]:  # Has consultation code
                consultation_codes.add(parts[1])

        # Format for dropdown
        return [{"text": code, "value": code} for code in sorted(consultation_codes)]
    except Exception:
        logger.exception("Failed to get consultation codes from S3")
        return []


def validate_consultation_structure(
    bucket_name: str, consultation_code: str, timestamp: str
) -> tuple[bool, list[str]]:
    """
    Validates that the S3 structure contains all required files for import.

    Returns:
        tuple: (is_valid, error_messages)
    """
    s3 = boto3.client("s3")
    errors = []

    # Define required structure
    base_path = f"app_data/{consultation_code}/"
    inputs_path = f"{base_path}inputs/"
    outputs_path = f"{base_path}outputs/mapping/{timestamp}/"

    required_files = {
        "respondents": f"{inputs_path}respondents.jsonl",
    }

    required_outputs = ["themes.json", "mapping.jsonl", "sentiment.jsonl", "detail_detection.jsonl"]

    try:
        # Check if respondents file exists
        try:
            s3.head_object(Bucket=bucket_name, Key=required_files["respondents"])
        except s3.exceptions.NoSuchKey:
            errors.append(f"Missing required file: {required_files['respondents']}")
        except Exception as e:
            errors.append(f"Error checking respondents file: {str(e)}")

        # Get all question part folders
        question_folders = get_question_folders(inputs_path, bucket_name)

        if not question_folders:
            errors.append(f"No question_part folders found in {inputs_path}")

        # Check each question part has required input files
        for folder in question_folders:
            question_num = folder.split("/")[-2]

            # Check input files
            question_file = f"{folder}question.json"
            responses_file = f"{folder}responses.jsonl"

            try:
                s3.head_object(Bucket=bucket_name, Key=question_file)
            except s3.exceptions.NoSuchKey:
                errors.append(f"Missing {question_file}")
            except Exception as e:
                errors.append(f"Error checking {question_file}: {str(e)}")

            try:
                s3.head_object(Bucket=bucket_name, Key=responses_file)
            except s3.exceptions.NoSuchKey:
                errors.append(f"Missing {responses_file}")
            except Exception as e:
                errors.append(f"Error checking {responses_file}: {str(e)}")

            # Check output files for this question part
            output_folder = f"{outputs_path}{question_num}/"
            for output_file in required_outputs:
                output_key = f"{output_folder}{output_file}"
                try:
                    s3.head_object(Bucket=bucket_name, Key=output_key)
                except s3.exceptions.NoSuchKey:
                    errors.append(f"Missing output file: {output_key}")
                except Exception as e:
                    errors.append(f"Error checking {output_key}: {str(e)}")

        # Validate JSON/JSONL files are parseable (spot check first question part)
        if question_folders and not errors:
            first_folder = question_folders[0]

            # Check question.json is valid JSON
            try:
                response = s3.get_object(Bucket=bucket_name, Key=f"{first_folder}question.json")
                json.loads(response["Body"].read())
            except json.JSONDecodeError:
                errors.append(f"Invalid JSON in {first_folder}question.json")
            except Exception as e:
                errors.append(f"Error reading {first_folder}question.json: {str(e)}")

            # Check first line of responses.jsonl is valid
            try:
                response = s3.get_object(Bucket=bucket_name, Key=f"{first_folder}responses.jsonl")
                first_line = response["Body"].iter_lines().__next__()
                json.loads(first_line.decode("utf-8"))
            except json.JSONDecodeError:
                errors.append(f"Invalid JSONL in {first_folder}responses.jsonl")
            except StopIteration:
                errors.append(f"Empty file: {first_folder}responses.jsonl")
            except Exception as e:
                errors.append(f"Error reading {first_folder}responses.jsonl: {str(e)}")

    except Exception as e:
        errors.append(f"Unexpected error during validation: {str(e)}")

    is_valid = len(errors) == 0
    return is_valid, errors


def bulk_create_response_annotation(
    question_id: UUID, sentiment_dict, evidence_dict, mapping_dict
) -> list[tuple[UUID, str]]:
    annotation_theme_mappings: list[tuple[UUID, str]] = []

    responses = Response.objects.filter(question_id=question_id).values_list(
        "id", "respondent__themefinder_id"
    )

    objs_to_save = []
    for response_id, themefinder_id in responses:
        annotation = ResponseAnnotation(
            response_id=response_id,
            sentiment=sentiment_dict.get(themefinder_id, ResponseAnnotation.Sentiment.UNCLEAR),
            evidence_rich=evidence_dict.get(themefinder_id, ResponseAnnotation.EvidenceRich.NO),
            human_reviewed=False,
        )
        objs_to_save.append(annotation)

        for key in mapping_dict.get(themefinder_id, []):
            annotation_theme_mappings.append((annotation.id, key))

        if len(objs_to_save) >= 1000:
            ResponseAnnotation.objects.bulk_create(objs_to_save)
            objs_to_save = []

    ResponseAnnotation.objects.bulk_create(objs_to_save)
    return annotation_theme_mappings


def bulk_create_response_annotation_themes(
    annotation_theme_mappings: list[tuple[UUID, str]], question_id: UUID
):
    existing_themes = Theme.objects.filter(question_id=question_id).values_list("key", "pk")

    theme_keys = dict(existing_themes)

    objs_to_save = []
    for annotation_id, key in annotation_theme_mappings:
        if theme_id := theme_keys.get(key):
            response_annotation_theme = ResponseAnnotationTheme.objects.create(
                response_annotation_id=annotation_id, theme_id=theme_id
            )
            objs_to_save.append(response_annotation_theme)

        if len(objs_to_save) >= 1000:
            ResponseAnnotationTheme.objects.bulk_create(objs_to_save)
            objs_to_save = []

    ResponseAnnotationTheme.objects.bulk_create(objs_to_save)


def import_mapping(
    question_id: UUID,
    outputs_path: str,
):
    """
    Import mapping data for a Consultation Question

    Args:
        question_id: Question object for mapping
        outputs_path: S3 folder name containing the output data
    """
    s3_client = boto3.client("s3")

    question = Question.objects.get(pk=question_id)
    output_folder = f"{outputs_path}question_part_{question.number}/"
    logger.info(
        f"Starting mapping import for consultation {question.consultation.id}, question {question_id})"
    )

    try:
        mapping_file_key = f"{output_folder}mapping.jsonl"
        sentiment_file_key = f"{output_folder}sentiment.jsonl"
        evidence_file_key = f"{output_folder}detail_detection.jsonl"

        # Read all annotation data
        mapping_response = s3_client.get_object(Bucket=bucket_name, Key=mapping_file_key)
        mapping_dict = {}
        for line in mapping_response["Body"].iter_lines():
            mapping = json.loads(line.decode("utf-8"))
            mapping_dict[mapping["themefinder_id"]] = mapping.get("theme_keys", [])

        sentiment_response = s3_client.get_object(Bucket=bucket_name, Key=sentiment_file_key)
        sentiment_dict = {}
        for line in sentiment_response["Body"].iter_lines():
            sentiment = json.loads(line.decode("utf-8"))
            sentiment_value = sentiment.get("sentiment", "UNCLEAR").upper()

            if sentiment_value == "AGREEMENT":
                sentiment_dict[sentiment["themefinder_id"]] = ResponseAnnotation.Sentiment.AGREEMENT
            elif sentiment_value == "DISAGREEMENT":
                sentiment_dict[sentiment["themefinder_id"]] = (
                    ResponseAnnotation.Sentiment.DISAGREEMENT
                )
            else:
                sentiment_dict[sentiment["themefinder_id"]] = ResponseAnnotation.Sentiment.UNCLEAR

        evidence_response = s3_client.get_object(Bucket=bucket_name, Key=evidence_file_key)
        evidence_dict = {}
        for line in evidence_response["Body"].iter_lines():
            evidence = json.loads(line.decode("utf-8"))
            evidence_value = evidence.get("evidence_rich", "NO").upper()
            evidence_dict[evidence["themefinder_id"]] = (
                ResponseAnnotation.EvidenceRich.YES
                if evidence_value == "YES"
                else ResponseAnnotation.EvidenceRich.NO
            )

        # Create annotations
        annotation_theme_mappings = bulk_create_response_annotation(
            question_id, sentiment_dict, evidence_dict, mapping_dict
        )

        # Add theme relationships
        bulk_create_response_annotation_themes(annotation_theme_mappings, question_id)

    except Exception as e:
        logger.error(
            f"Error importing mapping for consultation {question.consultation.id}, question {question_id}: {str(e)}"
        )
        raise


def import_responses(question_id: UUID, question_folder: str):
    """
    Batch Safe Import response data for a Consultation Question.

    Args:
        question_id: Question for response
        question_folder: list of responses data
    """
    s3_client = boto3.client("s3")

    question = Question.objects.get(pk=question_id)

    logger.info(
        f"Getting responses data for consultation {question.consultation.id}, question {question_id}"
    )
    responses_file_key = f"{question_folder}responses.jsonl"

    response = s3_client.get_object(Bucket=bucket_name, Key=responses_file_key)
    responses_to_save = []

    for line in response["Body"].iter_lines():
        response_data = json.loads(line.decode("utf-8"))
        themefinder_id = response_data["themefinder_id"]
        respondent = Respondent.objects.get(
            consultation=question.consultation, themefinder_id=themefinder_id
        )

        response = Response(
            respondent_id=respondent.id,
            question_id=question_id,
            free_text=response_data.get("text", ""),
            chosen_options=response_data.get("chosen_options", []),
        )

        responses_to_save.append(response)

        if len(responses_to_save) >= DEFAULT_BATCH_SIZE:
            Response.objects.bulk_create(responses_to_save)
            responses_to_save = []

    if responses_to_save:
        Response.objects.bulk_create(responses_to_save)


def import_themes(question_id: UUID, outputs_path: str):
    s3_client = boto3.client("s3")
    question = Question.objects.get(pk=question_id)
    themes_file_key = f"{outputs_path}question_part_{question.number}/themes.json"

    response = s3_client.get_object(Bucket=bucket_name, Key=themes_file_key)
    theme_data = json.loads(response["Body"].read())

    themes_to_save = []
    for theme in theme_data:
        themes_to_save.append(
            Theme(
                question_id=question_id,
                name=theme["theme_name"],
                description=theme["theme_description"],
                key=theme["theme_key"],
            )
        )

    themes = Theme.objects.bulk_create(themes_to_save)
    logger.info(f"Imported {len(themes)} themes for question {question_id}")


def import_questions(
    consultation_id: UUID,
    consultation_code: str,
    timestamp: str,
):
    """
    Import question data for a consultation.

    Args:
        consultation_id: Consultation for questions
        consultation_code: S3 folder name containing the consultation data
        timestamp: Timestamp folder name for the AI outputs
    """
    s3_client = boto3.client("s3")

    logger.info(f"Starting question import for consultation {consultation_id})")

    base_path = f"app_data/{consultation_code}/"
    inputs_path = f"{base_path}inputs/"
    outputs_path = f"{base_path}outputs/mapping/{timestamp}/"

    try:
        question_folders = get_question_folders(inputs_path, bucket_name)

        for question_folder in question_folders:
            question_num_str = question_folder.split("/")[-2].replace("question_part_", "")
            question_number = int(question_num_str)

            logger.info(f"Processing question {question_number}")

            question_file_key = f"{question_folder}question.json"
            response = s3_client.get_object(Bucket=bucket_name, Key=question_file_key)
            question_data = json.loads(response["Body"].read())

            question_text = question_data.get("question_text", "")
            if not question_text:
                raise ValueError(f"Question text is required for question {question_number}")

            question = Question.objects.create(
                consultation_id=consultation_id,
                text=question_text,
                slug=f"question-{question_number}",
                number=question_number,
                has_free_text=True,  # Default for now
                has_multiple_choice=False,  # Default for now
                multiple_choice_options=None,
            )

            import_themes(question.id, outputs_path)

            import_responses(question.id, question_folder)

            import_mapping(
                question.id,
                outputs_path,
            )

        logger.info(f"Imported {len(question_folders)} questions")

    except Exception as e:
        logger.error(f"Error importing question data for {consultation_code}: {str(e)}")
        raise


def import_respondents(consultation_id: UUID, consultation_code: str):
    """
    Batch safe Import respondent data for a consultation.
    """
    s3_client = boto3.client("s3")

    logger.info(f"Starting import_respondents batch for consultation {consultation_id}")

    respondents_file_key = f"app_data/{consultation_code}/inputs/respondents.jsonl"
    response = s3_client.get_object(Bucket=bucket_name, Key=respondents_file_key)

    batch_size = 1000
    respondents_batch = []

    for line in response["Body"].iter_lines():
        respondent_data = json.loads(line.decode("utf-8"))
        respondents_batch.append(
            Respondent(
                consultation_id=consultation_id,
                themefinder_id=respondent_data["themefinder_id"],
                demographics=respondent_data.get("demographic_data", {}),
            )
        )

        # Process batch when it reaches the limit
        if len(respondents_batch) >= batch_size:
            Respondent.objects.bulk_create(respondents_batch, batch_size=batch_size)
            respondents_batch = []  # Clear the batch
            logger.info(f"Processed batch of {batch_size} respondents")

    # Don't forget the final batch if it's not empty
    if respondents_batch:
        Respondent.objects.bulk_create(respondents_batch, batch_size=len(respondents_batch))
        logger.info(f"Processed final batch of {len(respondents_batch)} respondents")


def create_consultation(
    consultation_name: str,
    consultation_code: str,
    current_user_id: int,
    timestamp: str,
):
    """
    Create a consultation.

    Args:
        consultation_name: Display name for the consultation
        consultation_code: S3 folder name containing the consultation data
        current_user_id: ID of the user initiating the import
        timestamp: Timestamp folder name for the AI outputs
    """
    try:
        logger.info(
            f"Starting consultation import: {consultation_name} (code: {consultation_code})"
        )

        consultation = Consultation.objects.create(title=consultation_name)

        # Add the current user to the consultation
        from consultation_analyser.authentication.models import User

        user = User.objects.get(id=current_user_id)
        consultation.users.add(user)

        logger.info(f"Created consultation: {consultation.title} (ID: {consultation.id})")

        logger.info(f"Getting respondents data for: {consultation.title} (ID: {consultation.id})")

        import_respondents(consultation.id, consultation_code)

        import_questions(
            consultation.id,
            consultation_code,
            timestamp,
        )

    except Exception as e:
        logger.error(f"Error importing consultation {consultation_name}: {str(e)}")
        raise
