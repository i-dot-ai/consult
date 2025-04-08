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


def get_themefinder_outputs_for_question(
    question_folder_key: str, output_name: str
) -> dict | list[dict]:
    data_key = f"{question_folder_key}{output_name}.json"
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=data_key)
    return json.loads(response["Body"].read())


def import_question_part_data(consultation: Consultation, question_part_dict: dict):
    # TODO maybe some validation of question_part_dict - Pydantic models from ThemeFinder?
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
    question_part_type = question_part_dict["question_part_type"]
    question_part_type = type_mapping[question_part_type]

    question, _ = Question.objects.get_or_create(
        consultation=consultation, number=question_number, defaults={"text": question_text}
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


def import_responses(question_part: QuestionPart, responses_data: list[dict]):
    # TODO - ideally would have imported respondents separately
    consultation = question_part.question.consultation
    answers = []
    for response in responses_data:
        themefinder_respondent_id = response["themefinder_id"]
        respondent, _ = Respondent.objects.get_or_create(
            consultation=consultation, themefinder_respondent_id=themefinder_respondent_id
        )
        response_text = response["response"]
        # TODO - add import of options for non-free-text data
        # response_chosen_options = responses_data.get("options")
        answers.append(
            Answer(question_part=question_part, respondent=respondent, text=response_text)
        )
    Answer.objects.bulk_create(answers)
    logger.info(
        f"Saved responses for question_number {question_part.question.number} and question part {question_part.number}"
    )
    logger.info(
        f"Saved responses from themefinder_respondent_id {responses_data[0]['themefinder_id']} to {responses_data[-1]['themefinder_id']}"
    )


@job("default", timeout=900)
def import_responses_job(question_part: QuestionPart, responses_data: list[dict]):
    import_responses(question_part, responses_data)


def import_for_question_part(consultation: Consultation, question_part_folder_key: str):
    s3 = boto3.client("s3")
    # read question_data
    data_key = f"{question_part_folder_key}question.json"
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=data_key)
    question_part_data = json.loads(response["Body"].read())
    question_part = import_question_part_data(
        consultation=consultation, question_part_dict=question_part_data
    )
    return question_part
