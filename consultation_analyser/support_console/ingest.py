import json
import logging

import boto3
from django.conf import settings
from django_rq import job

from consultation_analyser.consultations.models import (
    Answer,
    Consultation,
    Question,
    QuestionPart,
    Respondent,
    SentimentMapping,
    ThemeMapping,
)

logger = logging.getLogger("import")


STANCE_MAPPING = {
    "POSITIVE": ThemeMapping.Stance.POSITIVE,
    "NEGATIVE": ThemeMapping.Stance.NEGATIVE,
}

SENTIMENT_MAPPING = {
    "agreement": SentimentMapping.Position.AGREEMENT,
    "disagreement": SentimentMapping.Position.DISAGREEMENT,
    "unclear": SentimentMapping.Position.UNCLEAR,
}


def get_all_question_part_subfolders(folder_name: str, bucket_name: str) -> list:
    s3 = boto3.resource("s3")
    objects = s3.Bucket(bucket_name).objects.filter(Prefix=folder_name)
    object_names_set = {obj.key for obj in objects}
    # Get set of all subfolders
    subfolders = set()
    for path in object_names_set:
        folder = "/".join(path.split("/")[:-1]) + "/"
        subfolders.add(folder)
    # Only the ones that are question_folders
    question_folders = [
        name for name in subfolders if name.split("/")[-2].startswith("question_part_")
    ]
    question_folders.sort()
    return question_folders


def get_all_folder_names_within_folder(
    folder_name: str, bucket_name: str
) -> set:
    s3 = boto3.resource("s3")
    objects = s3.Bucket(bucket_name).objects.filter(Prefix=folder_name)
    set_object_names = {obj.key for obj in objects}
    # Folders end in slash
    folders_only = {name for name in set_object_names if name.endswith("/")}
    # Exclude the name for the folder itself
    folder_names = {name.split("/")[1] for name in folders_only}
    folder_names = folder_names - {""}
    return folder_names




def get_themefinder_outputs_for_question(
    question_folder_key: str, output_name: str
) -> dict | list[dict]:
    data_key = f"{question_folder_key}{output_name}.json"
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=data_key)
    return json.loads(response["Body"].read())


def import_respondent_data(consultation: Consultation, respondent_data: list):
    logger.info(f"Importing respondent data for consultation: {consultation.title}")
    respondents_to_save = []
    for respondent in respondent_data:
        respondent = json.loads(respondent.decode("utf-8"))
        themefinder_respondent_id = respondent["themefinder_id"]
        # TODO - add further fields e.g. user supplied ID
        respondents_to_save.append(
            Respondent(
                consultation=consultation, themefinder_respondent_id=themefinder_respondent_id
            )
        )
    Respondent.objects.bulk_create(respondents_to_save)
    logger.info(f"Saved batch of respondents for consultation: {consultation.title}")


def import_question_part_data(consultation: Consultation, question_part_dict: dict) -> QuestionPart:
    type_mapping = {
        "free_text": QuestionPart.QuestionType.FREE_TEXT,
        "single_option": QuestionPart.QuestionType.SINGLE_OPTION,
        "multiple_option": QuestionPart.QuestionType.MULTIPLE_OPTIONS,
    }

    question_text = question_part_dict.get("question_text", "")
    question_part_text = question_part_dict.get("question_part_text", "")
    if not question_text and not question_part_text:
        raise ValueError("There is no text for question or question part.")

    question_number = question_part_dict["question_number"]
    question_part_number = question_part_dict.get(
        "question_part_number", 1
    )  # If no question_part_number, assume 1
    question_part_type = question_part_dict.get("question_part_type", "free_text")
    question_part_type = type_mapping[question_part_type]

    question, _ = Question.objects.get_or_create(
        consultation=consultation, number=question_number, text=question_text
    )

    if question_part_type == QuestionPart.QuestionType.FREE_TEXT:
        question_part = QuestionPart.objects.create(
            question=question,
            number=question_part_number,
            type=question_part_type,
            text=question_part_text,
        )
    else:
        options = question_part_dict["options"]
        question_part = QuestionPart.objects.create(
            question=question,
            number=question_part_number,
            type=question_part_type,
            text=question_part_text,
            options=options,
        )
    logger.info(
        f"Question part imported: question_number {question_number}, part_number: {question_part_number}"
    )
    return question_part


def import_responses(question_part: QuestionPart, responses_data: list) -> None:
    logger.info(
        f"Importing batch of responses for question_number {question_part.question.number} and question part {question_part.number}"
    )
    consultation = question_part.question.consultation

    # Respondents should have been imported already
    decoded_responses = [json.loads(response.decode("utf-8")) for response in responses_data]
    themefinder_ids = [response["themefinder_id"] for response in decoded_responses]
    corresponding_respondents = Respondent.objects.filter(consultation=consultation).filter(themefinder_respondent_id__in=themefinder_ids)
    respondent_dictionary = {r.themefinder_respondent_id: r for r in corresponding_respondents}

    # TODO - "response" field will change to "text", will also need to add import of options for non-free-text data
    answers = [Answer(question_part=question_part, respondent=respondent_dictionary[response["themefinder_id"]], text=response["response"]) for response in decoded_responses]
    Answer.objects.bulk_create(answers)
    logger.info(
        f"Saved batch of responses for question_number {question_part.question.number} and question part {question_part.number}"
    )


@job("default", timeout=900)
def import_respondent_data_job(consultation: Consultation, respondent_data: list):
    import_respondent_data(consultation=consultation, respondent_data=respondent_data)


@job("default", timeout=900)
def import_responses_job(question_part: QuestionPart, responses_data: list):
    import_responses(question_part, responses_data)


def import_all_respondents_from_jsonl(
    consultation: Consultation, bucket_name: str, inputs_folder_key: str, batch_size: int
) -> None:
    logger.info(f"Importing respondents from {inputs_folder_key}, batch_size {batch_size}")
    respondents_file_key = f"{inputs_folder_key}respondents.jsonl"
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=respondents_file_key)
    lines = []
    for line in response["Body"].iter_lines():
        lines.append(line)
        if len(lines) == batch_size:
            import_respondent_data_job.delay(consultation=consultation, respondent_data=lines)
            lines = []
    if lines:  # Any remaining lines < batch size
        import_respondent_data_job.delay(consultation=consultation, respondent_data=lines)


def import_question_part(consultation: Consultation, question_part_folder_key: str) -> QuestionPart:
    s3 = boto3.client("s3")
    data_key = f"{question_part_folder_key}question.json"
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=data_key)
    question_part_data = json.loads(response["Body"].read())
    question_part = import_question_part_data(
        consultation=consultation, question_part_dict=question_part_data
    )
    return question_part


def import_all_responses_from_jsonl(
    question_part: QuestionPart, bucket_name: str, question_part_folder_key: str, batch_size: int
) -> None:
    logger.info(f"Importing responses from {question_part_folder_key}, batch_size {batch_size}")
    responses_file_key = f"{question_part_folder_key}responses.jsonl"
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=responses_file_key)
    lines = []
    for line in response["Body"].iter_lines():
        lines.append(line)
        if len(lines) == batch_size:
            import_responses_job.delay(question_part=question_part, responses_data=lines)
            lines = []
    # Any remaining lines < batch size
    if lines:
        import_responses_job.delay(question_part=question_part, responses_data=lines)
