import json
import logging
from uuid import UUID

import boto3
import tiktoken
from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django_rq import get_queue

from consultation_analyser.consultations.models import (
    Consultation,
    DemographicOption,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    Theme,
)
from consultation_analyser.embeddings import embed_text

encoding = tiktoken.encoding_for_model("text-embedding-3-small")
logger = logging.getLogger("import")
DEFAULT_BATCH_SIZE = 10_000
DEFAULT_TIMEOUT_SECONDS = 3_600


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
        objects = s3.Bucket(settings.AWS_BUCKET_NAME).objects.filter(
            Prefix="app_data/consultations/"
        )

        # Get unique consultation folders
        consultation_codes = set()
        for obj in objects:
            parts = obj.key.split("/")
            if len(parts) >= 3 and parts[2]:  # Has consultation code
                consultation_codes.add(parts[2])

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
    base_path = f"app_data/consultations/{consultation_code}/"
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
                response = s3.get_object(Bucket=bucket_name, Key=question_file)
                question_data = json.loads(response["Body"].read())
                has_free_text = question_data.get("has_free_text", True)
            except s3.exceptions.NoSuchKey:
                errors.append(f"Missing {question_file}")
                has_free_text = True
            except Exception as e:
                errors.append(f"Error checking {question_file}: {str(e)}")
                has_free_text = True

            try:
                s3.head_object(Bucket=bucket_name, Key=responses_file)
            except s3.exceptions.NoSuchKey:
                errors.append(f"Missing {responses_file}")
            except Exception as e:
                errors.append(f"Error checking {responses_file}: {str(e)}")

            # Check output files for this question part, if it is a free-text question
            if has_free_text:
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


def create_embeddings(consultation_id: UUID):
    queryset = Response.objects.filter(
        question__consultation_id=consultation_id, free_text__isnull=False
    )
    total = queryset.count()
    batch_size = 1_000

    for i in range(0, total, batch_size):
        responses = queryset.order_by("id")[i : i + batch_size]

        free_texts = [response.free_text or "" for response in responses]
        embeddings = embed_text(free_texts)

        for response, embedding in zip(responses, embeddings):
            response.embedding = embedding
            response.search_vector = SearchVector("free_text")

        Response.objects.bulk_update(responses, ["embedding", "search_vector"])


def import_response_annotation_themes(question: Question, output_folder: str):
    mapping_file_key = f"{output_folder}mapping.jsonl"
    s3_client = boto3.client("s3")

    mapping_response = s3_client.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=mapping_file_key)
    mapping_dict = {}
    for line in mapping_response["Body"].iter_lines():
        mapping = json.loads(line.decode("utf-8"))
        mapping_dict[mapping["themefinder_id"]] = mapping.get("theme_keys", [])

    objects_to_save = []

    theme_mappings = dict(Theme.objects.filter(question=question).values_list("key", "pk"))

    annotation_theme_mappings = ResponseAnnotation.objects.filter(
        response__question=question
    ).values_list("id", "response__respondent__themefinder_id")

    for i, (response_annotation_id, themefinder_id) in enumerate(annotation_theme_mappings):
        for key in mapping_dict.get(themefinder_id, []):
            objects_to_save.append(
                ResponseAnnotationTheme(
                    response_annotation_id=response_annotation_id,
                    theme_id=theme_mappings[key],
                )
            )
            if len(objects_to_save) >= DEFAULT_BATCH_SIZE:
                ResponseAnnotationTheme.objects.bulk_create(objects_to_save)
                objects_to_save = []
                logger.info(
                    "saved %s ResponseAnnotationTheme for question %s", i + 1, question.number
                )

    ResponseAnnotationTheme.objects.bulk_create(objects_to_save)


def import_response_annotations(question: Question, output_folder: str):
    sentiment_file_key = f"{output_folder}sentiment.jsonl"
    evidence_file_key = f"{output_folder}detail_detection.jsonl"
    s3_client = boto3.client("s3")
    sentiment_response = s3_client.get_object(
        Bucket=settings.AWS_BUCKET_NAME, Key=sentiment_file_key
    )
    sentiment_dict = {}
    for line in sentiment_response["Body"].iter_lines():
        sentiment = json.loads(line.decode("utf-8"))
        sentiment_value = sentiment.get("sentiment", "UNCLEAR").upper()

        if sentiment_value == "AGREEMENT":
            sentiment_dict[sentiment["themefinder_id"]] = ResponseAnnotation.Sentiment.AGREEMENT
        elif sentiment_value == "DISAGREEMENT":
            sentiment_dict[sentiment["themefinder_id"]] = ResponseAnnotation.Sentiment.DISAGREEMENT
        else:
            sentiment_dict[sentiment["themefinder_id"]] = ResponseAnnotation.Sentiment.UNCLEAR

    evidence_response = s3_client.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=evidence_file_key)
    evidence_dict = {}
    for line in evidence_response["Body"].iter_lines():
        evidence = json.loads(line.decode("utf-8"))
        evidence_value = (evidence.get("evidence_rich") or "NO").upper()
        evidence_dict[evidence["themefinder_id"]] = (
            ResponseAnnotation.EvidenceRich.YES
            if evidence_value == "YES"
            else ResponseAnnotation.EvidenceRich.NO
        )

    # Create annotations
    responses = Response.objects.filter(question=question).values_list(
        "id", "respondent__themefinder_id"
    )
    # save_mapping_data
    annotations_to_save = []

    for i, (response_id, themefinder_id) in enumerate(responses):
        annotation = ResponseAnnotation(
            response_id=response_id,
            sentiment=sentiment_dict.get(themefinder_id, ResponseAnnotation.Sentiment.UNCLEAR),
            evidence_rich=evidence_dict.get(themefinder_id, ResponseAnnotation.EvidenceRich.NO),
            human_reviewed=False,
        )
        annotations_to_save.append(annotation)
        if len(annotations_to_save) >= DEFAULT_BATCH_SIZE:
            ResponseAnnotation.objects.bulk_create(annotations_to_save)
            annotations_to_save = []
            logger.info("saved %s ResponseAnnotations for question %s", i + 1, question.number)

    ResponseAnnotation.objects.bulk_create(annotations_to_save)


def _embed_responses(responses: list[dict]) -> list[Response]:
    embeddings = embed_text([r["free_text"] for r in responses])
    return [Response(embedding=embedding, **r) for r, embedding in zip(responses, embeddings)]


def import_responses(question: Question, responses_file_key: str):
    """
    Import response data for a Consultation Question.

    Args:
        question: Question object for response
        responses_file_key: s3key
    """
    s3_client = boto3.client("s3")

    responses_data = s3_client.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=responses_file_key)

    try:
        # Get respondents
        respondents = Respondent.objects.filter(consultation=question.consultation)
        respondent_dict = {r.themefinder_id: r for r in respondents}

        # Second pass: create responses
        # type: ignore
        responses_to_save: list = []  # type: ignore
        max_total_tokens = 100_000
        max_batch_size = 2048
        total_tokens = 0

        for i, line in enumerate(responses_data["Body"].iter_lines()):
            response_data = json.loads(line.decode("utf-8"))
            themefinder_id = response_data["themefinder_id"]

            if themefinder_id not in respondent_dict:
                logger.warning(f"No respondent found for themefinder_id: {themefinder_id}")
                continue

            free_text = response_data.get("text", "")
            if not free_text:
                logger.warning(f"Empty text for themefinder_id: {themefinder_id}")
                continue

            token_count = len(encoding.encode(free_text))
            if token_count > 8192:
                logger.warning(f"Truncated text for themefinder_id: {themefinder_id}")
                free_text = free_text[:1000]
                token_count = len(encoding.encode(free_text))

            if total_tokens + token_count > max_total_tokens or len(responses_to_save) >= max_batch_size:
                embedded_responses_to_save = _embed_responses(responses_to_save)
                Response.objects.bulk_create(embedded_responses_to_save)
                responses_to_save = []
                total_tokens = 0
                logger.info("saved %s Responses for question %s", i + 1, question.number)

            responses_to_save.append(
                dict(
                    respondent=respondent_dict[themefinder_id],
                    question=question,
                    free_text=free_text,
                    chosen_options=response_data.get("chosen_options", []),
                )
            )
            total_tokens += token_count

        # last batch
        embedded_responses_to_save = _embed_responses(responses_to_save)
        Response.objects.bulk_create(embedded_responses_to_save)

        # re-save the responses to ensure that every response has search_vector
        # i.e the lexical bit
        for response in Response.objects.filter(question=question):
            response.save()

    except Exception as e:
        logger.error(
            f"Error importing responses for consultation {question.consultation.title}, question {question.number}: {str(e)}"
        )
        raise


def import_themes(question: Question, output_folder: str):
    s3_client = boto3.client("s3")
    themes_file_key = f"{output_folder}themes.json"
    response = s3_client.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=themes_file_key)
    theme_data = json.loads(response["Body"].read())

    themes_to_save = []
    for theme in theme_data:
        themes_to_save.append(
            Theme(
                question=question,
                name=theme["theme_name"],
                description=theme["theme_description"],
                key=theme["theme_key"],
            )
        )

    themes = Theme.objects.bulk_create(themes_to_save)
    logger.info(f"Imported {len(themes)} themes for question {question.number}")


def import_questions(
    consultation: Consultation,
    consultation_code: str,
    timestamp: str,
):
    """
    Import question data for a consultation.
    Args:
        consultation: Consultation object for questions
        consultation_code: S3 folder name containing the consultation data
        timestamp: Timestamp folder name for the AI outputs
    """
    logger.info(f"Starting question import for consultation {consultation.title})")

    bucket_name = settings.AWS_BUCKET_NAME
    base_path = f"app_data/consultations/{consultation_code}/"
    outputs_path = f"{base_path}outputs/mapping/{timestamp}/"

    queue = get_queue(default_timeout=DEFAULT_TIMEOUT_SECONDS)

    try:
        s3_client = boto3.client("s3")
        question_folders = get_question_folders(
            f"app_data/consultations/{consultation_code}/inputs/", settings.AWS_BUCKET_NAME
        )

        for question_folder in question_folders:
            question_num_str = question_folder.split("/")[-2].replace("question_part_", "")
            question_number = int(question_num_str)

            logger.info(f"Processing question {question_number}")

            question_file_key = f"{question_folder}question.json"
            response = s3_client.get_object(Bucket=bucket_name, Key=question_file_key)
            question_data = json.loads(response["Body"].read())

            question_text = question_data.get("question_text", "")
            multiple_choice_options = question_data.get("options", [])
            if not question_text:
                raise ValueError(f"Question text is required for question {question_number}")

            question = Question.objects.create(
                consultation=consultation,
                text=question_text,
                slug=f"question-{question_number}",
                number=question_number,
                has_free_text=question_data.get("has_free_text", True),
                has_multiple_choice=bool(multiple_choice_options),
                multiple_choice_options=multiple_choice_options,
            )

            responses_file_key = f"{question_folder}responses.jsonl"
            responses = queue.enqueue(import_responses, question, responses_file_key)

            if question.has_free_text:
                output_folder = f"{outputs_path}question_part_{question_num_str}/"
                themes = queue.enqueue(import_themes, question, output_folder, depends_on=responses)
                response_annotations = queue.enqueue(
                    import_response_annotations, question, output_folder, depends_on=themes
                )
                queue.enqueue(
                    import_response_annotation_themes,
                    question,
                    output_folder,
                    depends_on=response_annotations,
                )

    except Exception as e:
        logger.error(f"Error importing question data for {consultation_code}: {str(e)}")
        raise


def import_respondents(consultation: Consultation, consultation_code: str):
    """
    Import respondent data for a consultation.

    Args:
        consultation: Consultation object for respondents
        consultation_code: list of respondent data
    """
    logger.info(f"Starting import_respondents batch for consultation {consultation.title})")

    s3_client = boto3.client("s3")
    respondents_file_key = f"app_data/consultations/{consultation_code}/inputs/respondents.jsonl"
    response = s3_client.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=respondents_file_key)

    respondents_to_save = []

    for i, line in enumerate(response["Body"].iter_lines()):
        respondent_data = json.loads(line.decode("utf-8"))
        themefinder_id = respondent_data.get("themefinder_id")
        demographics = respondent_data.get("demographic_data", {})

        respondents_to_save.append(
            Respondent(
                consultation=consultation,
                themefinder_id=themefinder_id,
                demographics=demographics,
            )
        )
        if len(respondents_to_save) >= DEFAULT_BATCH_SIZE:
            Respondent.objects.bulk_create(respondents_to_save)
            respondents_to_save = []
            logger.info("saved %s Respondents", i + 1)

    Respondent.objects.bulk_create(respondents_to_save)

    # Build demographic options from respondent data
    demographic_options_count = DemographicOption.rebuild_for_consultation(consultation)
    logger.info(f"Created {demographic_options_count} demographic options")


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

        import_respondents(consultation, consultation_code)

        import_questions(
            consultation,
            consultation_code,
            timestamp,
        )

    except Exception as e:
        logger.error(f"Error importing consultation {consultation_name}: {str(e)}")
        raise


def get_all_folder_names_within_folder(folder_name: str, bucket_name: str) -> set:
    s3 = boto3.client("s3")

    # Use list_objects_v2 with delimiter to get "folders" directly
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name, Delimiter="/")

    folder_names = set()

    # Get folder names from CommonPrefixes
    if "CommonPrefixes" in response:
        for prefix in response["CommonPrefixes"]:
            # Extract folder name by removing the base prefix and trailing slash
            folder_path = prefix["Prefix"]
            folder_name_only = folder_path.replace(folder_name, "").rstrip("/")
            if folder_name_only:
                folder_names.add(folder_name_only)

    return folder_names


def get_folder_names_for_dropdown() -> list[dict]:
    try:
        consultation_folder_names = get_all_folder_names_within_folder(
            folder_name="app_data/consultations/", bucket_name=settings.AWS_BUCKET_NAME
        )
    except RuntimeError:  # If no credentials for AWS
        consultation_folder_names = set()
    consultation_folders_formatted = [{"text": x, "value": x} for x in consultation_folder_names]
    return consultation_folders_formatted


def send_job_to_sqs(consultation_code: str, job_type: str) -> dict:
    # SQS configuration - you should move these to settings.py
    QUEUE_URL = settings.SQS_QUEUE_URL

    # Choose environment variables based on job_type
    if job_type == "SIGNOFF":
        job_name = settings.SIGN_OFF_BATCH_JOB_NAME
        job_queue = settings.SIGN_OFF_BATCH_JOB_QUEUE
        job_definition = settings.SIGN_OFF_BATCH_JOB_DEFINITION
    else:
        job_name = settings.MAPPING_BATCH_JOB_NAME
        job_queue = settings.MAPPING_BATCH_JOB_QUEUE
        job_definition = settings.MAPPING_BATCH_JOB_DEFINITION

    # Message body with the consultation_code
    message_body = {
        "jobName": job_name,
        "jobQueue": job_queue,
        "jobDefinition": job_definition,
        "containerOverrides": {"command": ["--subdir", consultation_code, "--job-type", job_type]},
    }

    # Create SQS client
    sqs = boto3.client("sqs")

    try:
        # Send message to SQS
        logger.info(f"Sending message to SQS: {json.dumps(message_body)}")
        response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message_body))

        logger.info(f"Message sent to SQS. MessageId: {response['MessageId']}")
        return response

    except Exception as e:
        logger.error(f"Error sending message to SQS: {str(e)}")
        raise e
