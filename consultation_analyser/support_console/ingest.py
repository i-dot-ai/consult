import json
import re
from uuid import UUID

import boto3
import tiktoken
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django_rq import get_queue
from simple_history.utils import bulk_create_with_history
from themefinder import models
from themefinder.models import Position

from consultation_analyser.consultations.models import (
    CandidateTheme,
    Consultation,
    CrossCuttingTheme,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)
from consultation_analyser.embeddings import embed_text
from consultation_analyser.support_console.file_models import (
    DetailDetection,
    SentimentRecord,
    read_from_s3,
)

encoding = tiktoken.encoding_for_model("text-embedding-3-small")

logger = settings.LOGGER
DEFAULT_BATCH_SIZE = 10_000
DEFAULT_TIMEOUT_SECONDS = 3_600


def s3_key_exists(key: str) -> bool:
    s3_client = boto3.client("s3")
    try:
        s3_client.head_object(Bucket=settings.AWS_BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise  # Re-raise if it's a different error


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
            if match := re.search(
                r"^app_data\/consultations\/(\w+)",
                str(obj.key),
            ):
                consultation_codes.add(match.groups()[0])

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

    required_outputs = ["themes.json", "mapping.jsonl", "detail_detection.jsonl"]

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
            multiple_choice_file = f"{folder}multi_choice.jsonl"

            try:
                response = s3.get_object(Bucket=bucket_name, Key=question_file)
                question_data = json.loads(response["Body"].read())
                has_free_text = question_data.get("has_free_text", True)
                multiple_choice_options = question_data.get("options", [])
                has_multiple_choice = True if multiple_choice_options else False
            except s3.exceptions.NoSuchKey:
                errors.append(f"Missing {question_file}")
                has_free_text = True
                has_multiple_choice = False
            except Exception as e:
                errors.append(f"Error checking {question_file}: {str(e)}")
                has_free_text = True
                has_multiple_choice = False

            try:
                s3.head_object(Bucket=bucket_name, Key=responses_file)
            except s3.exceptions.NoSuchKey:
                errors.append(f"Missing {responses_file}")
            except Exception as e:
                errors.append(f"Error checking {responses_file}: {str(e)}")

            if has_multiple_choice:
                try:
                    s3.head_object(Bucket=bucket_name, Key=multiple_choice_file)
                except s3.exceptions.NoSuchKey:
                    errors.append(f"Missing {multiple_choice_file}")
                except Exception as e:
                    errors.append(f"Error checking {multiple_choice_file}: {str(e)}")

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


def create_embeddings_for_question(question_id: UUID):
    queryset = Response.objects.filter(question_id=question_id, free_text__isnull=False)
    total = queryset.count()
    batch_size = 1_000

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


def import_response_annotation_themes(question: Question):
    s3_client = boto3.client("s3")

    try:
        mapping_response = s3_client.get_object(
            Bucket=settings.AWS_BUCKET_NAME, Key=question.mapping_file
        )
    except Exception:
        raise KeyError("could not find file =", question.mapping_file)

    mapping_dict = {}
    for line in mapping_response["Body"].iter_lines():
        mapping = json.loads(line.decode("utf-8"))
        mapping_dict[mapping["themefinder_id"]] = mapping.get("theme_keys", [])

    objects_to_save = []

    theme_mappings = dict(SelectedTheme.objects.filter(question=question).values_list("key", "pk"))

    annotation_theme_mappings = ResponseAnnotation.objects.filter(
        response__question=question
    ).values_list("id", "response__respondent__themefinder_id")

    for i, (response_annotation_id, themefinder_id) in enumerate(annotation_theme_mappings):
        for key in mapping_dict.get(themefinder_id, []):
            if theme_id := theme_mappings.get(key):
                objects_to_save.append(
                    ResponseAnnotationTheme(
                        response_annotation_id=response_annotation_id,
                        theme_id=theme_id,
                    )
                )
            else:
                logger.warning("key {key} missing from mapping", key=key)

            if len(objects_to_save) >= DEFAULT_BATCH_SIZE:
                bulk_create_with_history(
                    objects_to_save, ResponseAnnotationTheme, ignore_conflicts=True
                )
                objects_to_save = []
                logger.info(
                    "saved {i} ResponseAnnotationTheme for question {question_number}",
                    i=i + 1,
                    question_number=question.number,
                )

    bulk_create_with_history(objects_to_save, ResponseAnnotationTheme, ignore_conflicts=True)


def import_response_annotations(question: Question):
    s3_client = boto3.client("s3")

    # Check if sentiment file exists and process it
    sentiment_dict = {}
    for sentiment in read_from_s3(
        SentimentRecord,
        s3_client,
        settings.AWS_BUCKET_NAME,
        question.sentiment_file,
        raise_error_if_file_missing=False,
    ):
        sentiment_dict[sentiment.themefinder_id] = sentiment.sentiment_enum

    evidence_dict = {}
    for evidence in read_from_s3(
        DetailDetection,
        s3_client,
        settings.AWS_BUCKET_NAME,
        question.detail_detection_file,
        raise_error_if_file_missing=False,
    ):
        evidence_dict[evidence.themefinder_id] = evidence.evidence_rich_bool

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
            evidence_rich=evidence_dict.get(themefinder_id, False),
            human_reviewed=False,
        )
        annotations_to_save.append(annotation)
        if len(annotations_to_save) >= DEFAULT_BATCH_SIZE:
            bulk_create_with_history(annotations_to_save, ResponseAnnotation)
            annotations_to_save = []
            logger.info(
                "saved {i} ResponseAnnotations for question {question_number}",
                i=i + 1,
                question_number=question.number,
            )

    bulk_create_with_history(annotations_to_save, ResponseAnnotation)


def read_response_file(responses_file_key: str) -> dict[str, str]:
    s3_client = boto3.client("s3")

    try:
        responses_data = s3_client.get_object(
            Bucket=settings.AWS_BUCKET_NAME, Key=responses_file_key
        )
    except s3_client.exceptions.NoSuchKey:
        return {}

    text_response_dict = {}
    for line in responses_data["Body"].iter_lines():
        response_data = json.loads(line.decode("utf-8"))
        themefinder_id = response_data["themefinder_id"]
        if free_text := response_data.get("text"):
            assert isinstance(free_text, str)
            text_response_dict[themefinder_id] = free_text
    return text_response_dict


def read_multi_choice_response_file(responses_file_key: str) -> dict[str, list[str]]:
    s3_client = boto3.client("s3")

    try:
        responses_data = s3_client.get_object(
            Bucket=settings.AWS_BUCKET_NAME, Key=responses_file_key
        )
    except s3_client.exceptions.NoSuchKey:
        return {}

    multi_choice_response_dict = {}
    for line in responses_data["Body"].iter_lines():
        response_data = json.loads(line.decode("utf-8"))
        themefinder_id = response_data["themefinder_id"]
        if chosen_options := response_data.get("options"):
            assert isinstance(chosen_options, list)
            multi_choice_response_dict[themefinder_id] = chosen_options
    return multi_choice_response_dict


def merge_free_text_and_multi_choice(
    free_text: dict[str, str], multi_choice: dict[str, list[str]]
) -> list[tuple[str, str | None, list[str] | None]]:
    keys = set(free_text).union(multi_choice)
    return [(key, free_text.get(key), multi_choice.get(key)) for key in keys]


def import_responses(question: Question, responses_file_key: str, multichoice_file_key: str):
    """
    Import response data for a Consultation Question.

    Args:
        question: Question object for response
        responses_file_key: s3key
    """

    plain_response_dict = read_response_file(responses_file_key)

    multichoice_data = read_multi_choice_response_file(multichoice_file_key)
    responses = merge_free_text_and_multi_choice(plain_response_dict, multichoice_data)

    try:
        # Get respondents
        respondents = Respondent.objects.filter(consultation=question.consultation)
        respondent_dict = {r.themefinder_id: r for r in respondents}

        # Second pass: create responses
        # type: ignore
        responses_to_save: list = []  # type: ignore
        multi_choice_response_to_save: list[tuple[Response, list[str]]] = []  # type: ignore
        max_total_tokens = 100_000
        max_batch_size = 2048
        total_tokens = 0

        for i, (themefinder_id, free_text, chosen_options) in enumerate(responses):
            if themefinder_id not in respondent_dict:
                logger.warning(
                    "No respondent found for themefinder_id: {themefinder_id}",
                    themefinder_id=themefinder_id,
                )
                continue

            if free_text:
                token_count = len(encoding.encode(free_text))
                if token_count > 8192:
                    logger.warning(
                        "Truncated text for themefinder_id: {themefinder_id}",
                        themefinder_id=themefinder_id,
                    )
                    free_text = free_text[:1000]
                    token_count = len(encoding.encode(free_text))
            else:
                token_count = 0

            if (
                total_tokens + token_count > max_total_tokens
                or len(responses_to_save) >= max_batch_size
            ):
                Response.objects.bulk_create(responses_to_save)

                responses_to_save = []
                total_tokens = 0
                logger.info(
                    "saved {response_number} Responses for question {question_number}",
                    response_number=i + 1,
                    question_number=question.number,
                )

            response = Response(
                respondent=respondent_dict[themefinder_id],
                question=question,
                free_text=free_text,
            )

            if chosen_options:
                multi_choice_response_to_save.append((response, chosen_options))

            responses_to_save.append(response)
            total_tokens += token_count

        # last batch
        Response.objects.bulk_create(responses_to_save)
        for response, answers in multi_choice_response_to_save:
            chosen_options = MultiChoiceAnswer.objects.filter(question=question, text__in=answers)
            response.chosen_options.set(chosen_options)
            response.save()

        # re-save the responses to ensure that every response has search_vector
        # i.e the lexical bit
        for response in Response.objects.filter(question=question):
            response.save()

        # Update total_responses count for the question
        question.update_total_responses()
        logger.info(
            "Updated total_responses count for question {question_number}: {total_responses}",
            question_number=question.number,
            total_responses=question.total_responses,
        )

    except Exception as e:
        logger.error(
            "Error importing responses for consultation {question_consultation_title}, question {question_number}: {error}",
            question_consultation_title=question.consultation.title,
            question_number=question.number,
            error=e,
        )
        raise


def export_selected_themes(question: Question):
    s3_client = boto3.client("s3")

    themes_to_save = [
        models.Theme(
            topic_label=theme.name, topic_description=theme.description, position=Position.UNCLEAR
        )
        for theme in SelectedTheme.objects.filter(question=question)
    ]

    unique_topic_labels = {theme.topic_label for theme in themes_to_save}
    themes_to_save = [
        next(x for x in themes_to_save if x.topic_label == topic_label)
        for topic_label in unique_topic_labels
    ]

    themes = models.ThemeGenerationResponses(responses=themes_to_save)
    content = themes.model_dump_json()
    logger.info(
        "writing selected themes for question={number} to {file}",
        number=question.number,
        file=question.selected_themes_file,
    )

    s3_client.put_object(
        Bucket=settings.AWS_BUCKET_NAME, Key=question.selected_themes_file, Body=content
    )


def import_candidate_themes(question: Question):
    s3_client = boto3.client("s3")
    try:
        response = s3_client.get_object(
            Bucket=settings.AWS_BUCKET_NAME, Key=question.candidate_themes_file
        )
        theme_data = json.loads(response["Body"].read())
    except BaseException:
        logger.info("couldn't load file {file}", file=question.candidate_themes_file)
        return

    # First pass: create all themes without parent relationships
    topic_id_to_candidate_theme = {}
    themes_to_save = []
    for theme in theme_data:
        candidate_theme = CandidateTheme(
            question=question,
            name=theme["Theme Name"],
            description=theme["Theme Description"],
            approximate_frequency=theme["source_topic_count"],
        )
        themes_to_save.append(candidate_theme)

    created_themes = CandidateTheme.objects.bulk_create(themes_to_save)

    # Build mapping from topic_id to created CandidateTheme
    for theme, created_theme in zip(theme_data, created_themes):
        topic_id_to_candidate_theme[theme["topic_id"]] = created_theme

    # Second pass: set parent relationships
    themes_to_update = []
    for theme in theme_data:
        parent_id = theme.get("parent_id")
        if parent_id and parent_id != "0":
            candidate_theme = topic_id_to_candidate_theme[theme["topic_id"]]
            if parent_id in topic_id_to_candidate_theme:
                candidate_theme.parent = topic_id_to_candidate_theme[parent_id]
                themes_to_update.append(candidate_theme)

    if themes_to_update:
        CandidateTheme.objects.bulk_update(themes_to_update, ["parent"])

    logger.info(
        "Imported {len_themes} candidate themes for question {question_number}",
        len_themes=len(created_themes),
        question_number=question.number,
    )


def import_questions(
    consultation: Consultation,
    sign_off: bool = False,
):
    """
    Import question data for a consultation.
    Args:
        consultation: Consultation object for questions
        timestamp: Timestamp folder name for the AI outputs
        sign_off: If True, import candidate themes; if False, use standard theme import workflow
    """
    logger.info("Starting question import for consultation {title})", title=consultation.title)

    bucket_name = settings.AWS_BUCKET_NAME

    queue = get_queue(default_timeout=DEFAULT_TIMEOUT_SECONDS)

    try:
        s3_client = boto3.client("s3")
        question_folders = get_question_folders(
            f"app_data/consultations/{consultation.code}/inputs/", settings.AWS_BUCKET_NAME
        )

        for question_folder in question_folders:
            question_num_str = question_folder.split("/")[-2].replace("question_part_", "")
            question_number = int(question_num_str)

            logger.info("Processing question {question_number}", question_number=question_number)

            question_file_key = f"{question_folder}question.json"
            response = s3_client.get_object(Bucket=bucket_name, Key=question_file_key)
            question_data = json.loads(response["Body"].read())

            question_text = question_data.get("question_text", "")
            multi_choice_options = question_data.get("multi_choice_options", [])
            if not question_text:
                raise ValueError(f"Question text is required for question {question_number}")

            question = Question.objects.create(
                consultation=consultation,
                text=question_text,
                number=question_number,
                has_free_text=question_data.get("has_free_text", True),
                has_multiple_choice=bool(multi_choice_options),
                theme_status=Question.ThemeStatus.DRAFT,
            )
            for answer in multi_choice_options:
                MultiChoiceAnswer.objects.create(question=question, text=answer)

            responses_file_key = f"{question_folder}responses.jsonl"
            multiple_choice_file = f"{question_folder}multi_choice.jsonl"
            responses = queue.enqueue(
                import_responses, question, responses_file_key, multiple_choice_file
            )
            queue.enqueue(create_embeddings_for_question, question.id, depends_on=responses)

            if sign_off:
                import_candidate_themes(question)
            else:
                response_annotations = queue.enqueue(import_response_annotations, question)
                queue.enqueue(
                    import_response_annotation_themes,
                    question,
                    depends_on=response_annotations,
                )

    except Exception as e:
        logger.error(
            "Error importing question data for {consultation_code}: {error}",
            consultation_code=consultation.code,
            error=e,
        )
        raise


def import_cross_cutting_themes(consultation: Consultation):
    """
    Import cross-cutting themes that span across multiple questions.
    Must run after all themes have been imported.
    """
    logger.info(
        "Starting cross-cutting themes import for consultation {consultation_title}",
        consultation_title=consultation.title,
    )

    s3_client = boto3.client("s3")
    cct_file_key = f"{consultation.s3_mapping_folder}/cross_cutting_themes.json"

    try:
        # Check if file exists
        response = s3_client.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=cct_file_key)
        cct_data = json.loads(response["Body"].read())
    except s3_client.exceptions.NoSuchKey:
        logger.info("No cross_cutting_themes.json found, skipping cross-cutting themes import")
        return  # Don't fail, just skip
    except Exception as e:
        logger.error("Error reading cross-cutting themes file: {msg}", msg=e)
        raise

    # Get all questions for this consultation for lookup
    questions_dict = {q.number: q for q in Question.objects.filter(consultation=consultation)}

    for cct_entry in cct_data:
        # Create the cross-cutting theme
        cross_cutting_theme = CrossCuttingTheme.objects.create(
            consultation=consultation, name=cct_entry["name"], description=cct_entry["description"]
        )
        logger.info(
            "Created cross-cutting theme: {cross_cutting_theme_name}",
            cross_cutting_theme_name=cross_cutting_theme.name,
        )

        # Process themes dictionary: {question_number: [theme_keys]}
        themes_dict = cct_entry.get("themes", {})

        for question_number, theme_keys in themes_dict.items():
            # Find the question
            question = questions_dict.get(question_number)
            if not question:
                raise ValueError(
                    f"Question {question_number} not found for cross-cutting theme '{cct_entry['name']}'"
                )

            # Process each theme key for this question
            for theme_key in theme_keys:
                # Find the theme
                try:
                    theme = SelectedTheme.objects.get(question=question, key=theme_key)
                    theme.parent = cross_cutting_theme
                    theme.save()
                except SelectedTheme.DoesNotExist:
                    raise ValueError(
                        f"SelectedTheme {theme_key} not found for question {question_number} in cross-cutting theme '{cct_entry['name']}'"
                    )
                except SelectedTheme.MultipleObjectsReturned:
                    raise ValueError(
                        f"Multiple themes with key {theme_key} found for question {question_number} in cross-cutting theme '{cct_entry['name']}'"
                    )


def import_respondents(consultation: Consultation):
    """
    Import respondent data for a consultation.

    Args:
        consultation: Consultation object for respondents
    """
    logger.info(
        "Starting import_respondents batch for consultation {consultation_title})",
        consultation_title=consultation.title,
    )

    s3_client = boto3.client("s3")
    respondents_file_key = f"app_data/consultations/{consultation.code}/inputs/respondents.jsonl"
    response = s3_client.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=respondents_file_key)

    for i, line in enumerate(response["Body"].iter_lines()):
        respondent_data = json.loads(line.decode("utf-8"))
        themefinder_id = respondent_data.get("themefinder_id")
        demographics = respondent_data.get("demographic_data", {})

        respondent = Respondent.objects.create(
            consultation=consultation,
            themefinder_id=themefinder_id,
        )

        demographic_options = []
        for field_name, field_values in demographics.items():
            for field_value in field_values:
                demographic_option, _ = DemographicOption.objects.get_or_create(
                    consultation=consultation,
                    field_name=field_name,
                    field_value=field_value,
                )
                demographic_options.append(demographic_option)

        respondent.demographics.set(demographic_options)

        if i % 100 == 0:
            logger.error("imported {i} respondents", i=i)


def create_consultation(
    consultation_name: str,
    consultation_code: str,
    current_user_id: UUID,
    timestamp: str | None = None,
    sign_off: bool = False,
):
    """
    Create a consultation.

    Args:
        consultation_name: Display name for the consultation
        consultation_code: S3 folder name containing the consultation data
        current_user_id: ID of the user initiating the import
        timestamp: Timestamp folder name for the AI outputs
        sign_off: If True, import candidate themes; if False, use standard theme import workflow
    """
    try:
        logger.info(
            "Starting consultation import: {consultation_name} (code: {consultation_code})",
            consultation_name=consultation_name,
            consultation_code=consultation_code,
        )

        consultation = Consultation.objects.create(
            title=consultation_name,
            code=consultation_code,
            timestamp=timestamp,
            stage=Consultation.Stage.THEME_SIGN_OFF if sign_off else Consultation.Stage.ANALYSIS,
        )

        # Add the current user to the consultation
        from consultation_analyser.authentication.models import User

        user = User.objects.get(id=current_user_id)
        consultation.users.add(user)

        logger.info(
            "Created consultation: {consultation_title} (ID: {consultation_id})",
            consultation_title=consultation.title,
            consultation_id=consultation.id,
        )

        import_respondents(consultation)

        import_questions(
            consultation,
            sign_off,
        )

    except Exception as e:
        logger.error(
            "Error importing consultation {consultation_name}: {msg}",
            consultation_name=consultation_name,
            msg=e,
        )
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


def send_job_to_sqs(
    consultation_code: str, consultation_name: str, current_user_id: int, job_type: str
) -> dict:
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
        "userId": current_user_id,
        "consultationCode": consultation_code,
        "consultationName": consultation_name,
        "containerOverrides": {"command": ["--subdir", consultation_code, "--job-type", job_type]},
    }

    # Create SQS client
    sqs = boto3.client("sqs")

    try:
        # Send message to SQS
        logger.info("Sending message to SQS: {msg}", msg=json.dumps(message_body))
        response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message_body))

        logger.info("Message sent to SQS. MessageId: {msg}", msg=response["MessageId"])
        return response

    except Exception as e:
        logger.error("Error sending message to SQS: {error}", error=e)
        raise e
