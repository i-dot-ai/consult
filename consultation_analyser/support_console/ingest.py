import json
import logging

import boto3
from django.conf import settings
from django_rq import job

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    Theme,
)

logger = logging.getLogger("import")


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
    
    required_outputs = [
        "themes.json",
        "mapping.jsonl",
        "sentiment.jsonl",
        "detail_detection.jsonl"
    ]
    
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


def import_consultation(
    consultation_name: str, 
    consultation_code: str, 
    timestamp: str,
    current_user_id: int
) -> None:
    """
    Import a complete consultation including questions, respondents, responses, themes, and annotations.
    
    Args:
        consultation_name: Display name for the consultation
        consultation_code: S3 folder name containing the consultation data
        timestamp: Timestamp folder name for the AI outputs
        current_user_id: ID of the user initiating the import
    """
    logger.info(f"Starting consultation import: {consultation_name} (code: {consultation_code})")
    
    bucket_name = settings.AWS_BUCKET_NAME
    base_path = f"app_data/{consultation_code}/"
    inputs_path = f"{base_path}inputs/"
    outputs_path = f"{base_path}outputs/mapping/{timestamp}/"
    
    try:
        # 1. Create consultation
        consultation = Consultation.objects.create(title=consultation_name)
        
        # Add the current user to the consultation
        from consultation_analyser.authentication.models import User
        user = User.objects.get(id=current_user_id)
        consultation.users.add(user)
        
        logger.info(f"Created consultation: {consultation.title} (ID: {consultation.id})")
        
        # 2. Import respondents
        s3_client = boto3.client("s3")
        respondents_file_key = f"{inputs_path}respondents.jsonl"
        response = s3_client.get_object(Bucket=bucket_name, Key=respondents_file_key)
        
        respondents_to_save = []
        respondent_count = 0
        
        for line in response["Body"].iter_lines():
            respondent_data = json.loads(line.decode("utf-8"))
            themefinder_id = respondent_data.get("themefinder_id")
            demographics = respondent_data.get("demographic_data", {})
            
            respondents_to_save.append(
                Respondent(
                    consultation=consultation,
                    themefinder_id=themefinder_id,
                    demographics=demographics
                )
            )
            respondent_count += 1
        
        Respondent.objects.bulk_create(respondents_to_save)
        logger.info(f"Imported {respondent_count} respondents")
        
        # 3. Process each question
        question_folders = get_question_folders(inputs_path, bucket_name)
        
        for question_folder in question_folders:
            question_num_str = question_folder.split("/")[-2].replace("question_part_", "")
            question_number = int(question_num_str)
            
            logger.info(f"Processing question {question_number}")
            
            # 3a. Import question
            question_file_key = f"{question_folder}question.json"
            response = s3_client.get_object(Bucket=bucket_name, Key=question_file_key)
            question_data = json.loads(response["Body"].read())
            
            question_text = question_data.get("question_text", "")
            if not question_text:
                raise ValueError(f"Question text is required for question {question_number}")
            
            question = Question.objects.create(
                consultation=consultation,
                text=question_text,
                slug=f"question-{question_number}",
                number=question_number,
                has_free_text=True,  # Default for now
                has_multiple_choice=False,  # Default for now
                multiple_choice_options=None
            )
            
            # 3b. Import responses
            responses_file_key = f"{question_folder}responses.jsonl"
            response = s3_client.get_object(Bucket=bucket_name, Key=responses_file_key)
            
            # First pass: collect themefinder_ids
            response_lines = list(response["Body"].iter_lines())
            themefinder_ids = []
            for line in response_lines:
                response_data = json.loads(line.decode("utf-8"))
                themefinder_ids.append(response_data["themefinder_id"])
            
            # Get respondents
            respondents = Respondent.objects.filter(
                consultation=consultation,
                themefinder_id__in=themefinder_ids
            )
            respondent_dict = {r.themefinder_id: r for r in respondents}
            
            # Second pass: create responses
            responses_to_save = []
            for line in response_lines:
                response_data = json.loads(line.decode("utf-8"))
                themefinder_id = response_data["themefinder_id"]
                
                if themefinder_id not in respondent_dict:
                    logger.warning(f"No respondent found for themefinder_id: {themefinder_id}")
                    continue
                
                responses_to_save.append(
                    Response(
                        respondent=respondent_dict[themefinder_id],
                        question=question,
                        free_text=response_data.get("text", ""),
                        chosen_options=response_data.get("chosen_options", [])
                    )
                )
            
            Response.objects.bulk_create(responses_to_save)
            logger.info(f"Imported {len(responses_to_save)} responses for question {question_number}")
            
            # 3c. Import themes
            output_folder = f"{outputs_path}question_part_{question_num_str}/"
            themes_file_key = f"{output_folder}themes.json"
            response = s3_client.get_object(Bucket=bucket_name, Key=themes_file_key)
            theme_data = json.loads(response["Body"].read())
            
            themes_to_save = []
            for theme in theme_data:
                themes_to_save.append(
                    Theme(
                        question=question,
                        name=theme["theme_name"],
                        description=theme["theme_description"],
                        key=theme["theme_key"]
                    )
                )
            
            themes = Theme.objects.bulk_create(themes_to_save)
            theme_dict = {theme.key: theme for theme in themes}
            logger.info(f"Imported {len(themes)} themes for question {question_number}")
            
            # 3d. Import response annotations (combining mapping, sentiment, and evidence)
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
                    sentiment_dict[sentiment["themefinder_id"]] = ResponseAnnotation.Sentiment.DISAGREEMENT
                else:
                    sentiment_dict[sentiment["themefinder_id"]] = ResponseAnnotation.Sentiment.UNCLEAR
            
            evidence_response = s3_client.get_object(Bucket=bucket_name, Key=evidence_file_key)
            evidence_dict = {}
            for line in evidence_response["Body"].iter_lines():
                evidence = json.loads(line.decode("utf-8"))
                evidence_value = evidence.get("evidence_rich", "NO").upper()
                evidence_dict[evidence["themefinder_id"]] = (
                    ResponseAnnotation.EvidenceRich.YES if evidence_value == "YES" 
                    else ResponseAnnotation.EvidenceRich.NO
                )
            
            # Create annotations
            responses = Response.objects.filter(question=question)
            annotations_to_save = []
            annotation_theme_mappings = []
            
            for response_obj in responses:
                themefinder_id = response_obj.respondent.themefinder_id
                
                annotation = ResponseAnnotation(
                    response=response_obj,
                    sentiment=sentiment_dict.get(themefinder_id, ResponseAnnotation.Sentiment.UNCLEAR),
                    evidence_rich=evidence_dict.get(themefinder_id, ResponseAnnotation.EvidenceRich.NO),
                    human_reviewed=False
                )
                annotations_to_save.append(annotation)
                
                # Store theme mappings for after bulk create
                theme_keys = mapping_dict.get(themefinder_id, [])
                annotation_theme_mappings.append((annotation, theme_keys))
            
            # Bulk create annotations
            created_annotations = ResponseAnnotation.objects.bulk_create(annotations_to_save)
            
            # Add theme relationships
            for i, (annotation, theme_keys) in enumerate(annotation_theme_mappings):
                created_annotation = created_annotations[i]
                themes_to_add = [theme_dict[key] for key in theme_keys if key in theme_dict]
                
                if themes_to_add:
                    created_annotation.themes.set(themes_to_add)
            
            logger.info(f"Imported {len(created_annotations)} response annotations for question {question_number}")
        
        logger.info(f"Successfully completed import for consultation: {consultation_name}")
        
    except Exception as e:
        logger.error(f"Error importing consultation {consultation_name}: {str(e)}")
        raise