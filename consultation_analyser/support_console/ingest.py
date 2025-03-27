import json
import logging

import boto3
from django.conf import settings
from django_rq import job

from consultation_analyser.consultations.models import (
    Answer,
    Consultation,
    ExecutionRun,
    Framework,
    Question,
    QuestionPart,
    Respondent,
    SentimentMapping,
    Theme,
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


def get_all_question_subfolders(folder_name: str, bucket_name: str) -> list:
    s3 = boto3.resource("s3")
    objects = s3.Bucket(bucket_name).objects.filter(Prefix=folder_name)
    object_names_set = {obj.key for obj in objects}
    # Get set of all subfolders
    subfolders = set()
    for path in object_names_set:
        folder = "/".join(path.split("/")[:-1]) + "/"
        subfolders.add(folder)
    # Only the ones that are question_folders
    question_folders = [name for name in subfolders if name.split("/")[-2].startswith("question_")]
    question_folders.sort()
    return question_folders


def get_themefinder_outputs_for_question(
    question_folder_key: str, output_name: str
) -> dict | list[dict]:
    data_key = f"{question_folder_key}{output_name}.json"
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=data_key)
    return json.loads(response["Body"].read())


def import_themes(question_part: QuestionPart, theme_data: dict) -> Framework:
    theme_generation_execution_run = ExecutionRun.objects.create(
        type=ExecutionRun.TaskType.THEME_GENERATION
    )
    framework = Framework.create_initial_framework(
        question_part=question_part, execution_run=theme_generation_execution_run
    )
    for theme_key, theme_value in theme_data.items():
        name, description = theme_value.split(": ", 1)
        logger.info(f"Creating theme: {name}, key: {theme_key}")
        Theme.create_initial_theme(
            framework=framework, key=theme_key, name=name, description=description
        )
    return framework


def get_theme_for_key(framework: Framework, key: str) -> Theme:
    return Theme.objects.get(framework=framework, key=key)


def create_answer_from_dict(
    theme_mapping_dict: dict, question_part: QuestionPart, respondent: Respondent
) -> Answer:
    text = theme_mapping_dict["response"]
    answer = Answer.objects.create(question_part=question_part, respondent=respondent, text=text)
    return answer


def map_themes_to_answer(
    answer: Answer,
    theme_mapping_dict: dict,
    framework: Framework,
    mapping_execution_run: ExecutionRun,
) -> None:
    labels = theme_mapping_dict["labels"]
    stances = theme_mapping_dict["stances"]
    if len(labels) != len(stances):
        raise ValueError("Number of stances does not match number of themes")

    for label, raw_stance in zip(labels, stances):
        theme = get_theme_for_key(framework, label)
        stance = STANCE_MAPPING.get(raw_stance, "")
        # Theme mapping is unique on answer and theme
        ThemeMapping.objects.update_or_create(
            answer=answer,
            theme=theme,
            defaults={"stance": stance, "execution_run": mapping_execution_run},
        )


def import_theme_mapping_and_responses(
    framework: Framework,
    sentiment_execution_run: ExecutionRun,
    mapping_execution_run: ExecutionRun,
    theme_mapping_dict: dict,
) -> None:
    # TODO - check unique IDs
    question_part = framework.question_part
    consultation = question_part.question.consultation

    # Create respondent if doesn't exist, then create answer
    response_id = theme_mapping_dict["response_id"]
    respondent, _ = Respondent.objects.get_or_create(
        consultation=consultation, themefinder_respondent_id=response_id
    )
    answer = create_answer_from_dict(
        theme_mapping_dict=theme_mapping_dict, question_part=question_part, respondent=respondent
    )

    # Add sentiment to answer
    raw_position = theme_mapping_dict["position"]
    position = SENTIMENT_MAPPING.get(raw_position, "")
    SentimentMapping.objects.create(
        answer=answer, position=position, execution_run=sentiment_execution_run
    )

    # And map the themes
    map_themes_to_answer(
        answer=answer,
        theme_mapping_dict=theme_mapping_dict,
        framework=framework,
        mapping_execution_run=mapping_execution_run,
    )


def import_theme_mappings_for_framework(framework: Framework, list_mappings: list[dict]) -> None:
    sentiment_execution_run = ExecutionRun.objects.create(
        type=ExecutionRun.TaskType.SENTIMENT_ANALYSIS
    )
    mapping_execution_run = ExecutionRun.objects.create(type=ExecutionRun.TaskType.THEME_MAPPING)
    for theme_mapping_dict in list_mappings:
        logger.info(f"Importing theme mapping for response: {theme_mapping_dict}")
        import_theme_mapping_and_responses(
            framework=framework,
            sentiment_execution_run=sentiment_execution_run,
            mapping_execution_run=mapping_execution_run,
            theme_mapping_dict=theme_mapping_dict,
        )


def import_themefinder_data_for_question(
    consultation: Consultation, question_number: int, question_folder: str
) -> None:
    # Create question/question part
    question_data = get_themefinder_outputs_for_question(
        question_folder_key=question_folder, output_name="question"
    )
    if isinstance(question_data, dict):
        question_text = question_data.get("question")
    else:
        raise ValueError("Expected a dictionary of question data")
    # TODO - think about where to store text - in Question or QuestionPart - in question for now
    question = Question.objects.create(
        consultation=consultation, text=question_text, number=question_number
    )
    question_part = QuestionPart.objects.create(
        text="", question=question, type=QuestionPart.QuestionType.FREE_TEXT
    )
    # Import themes
    themes = get_themefinder_outputs_for_question(
        question_folder_key=question_folder, output_name="themes"
    )
    if isinstance(themes, dict):
        framework = import_themes(question_part=question_part, theme_data=themes)
    else:
        raise ValueError("Expected a dict of themes")
    logger.info(f"Imported themes for question {question_number}")

    # Import responses and mappings
    list_theme_mappings = get_themefinder_outputs_for_question(
        question_folder_key=question_folder, output_name="mapping"
    )
    if isinstance(list_theme_mappings, list):
        import_theme_mappings_for_framework(framework, list_theme_mappings)
    else:
        raise ValueError("Expected a list of dictionaries of theme mappings")
    logger.info(f"Imported themes for question {question_number}")
    logger.info(f"**Imported all data for question: {question.text}**")


@job("default", timeout=900)
def import_themefinder_data_for_question_job(
    consultation: Consultation, question_number: int, question_folder: str
) -> None:
    import_themefinder_data_for_question(
        consultation=consultation, question_number=question_number, question_folder=question_folder
    )
