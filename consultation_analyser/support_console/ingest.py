import json
import logging

import boto3
from django.conf import settings
from django_rq import job
from simple_history.utils import bulk_create_with_history

from consultation_analyser.consultations.models import (
    Answer,
    ConsultationOld,
    EvidenceRichMapping,
    ExecutionRun,
    Framework,
    QuestionOld,
    QuestionPart,
    RespondentOld,
    SentimentMapping,
    ThemeMapping,
    ThemeOld,
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
        "/".join(name.split("/")[:-1]) + "/"
        for name in subfolders
        if name.split("/")[-2].startswith("question_part_")
    ]
    question_folders.sort()
    return question_folders


def get_all_folder_names_within_folder(folder_name: str, bucket_name: str) -> set:
    s3 = boto3.resource("s3")
    objects = s3.Bucket(bucket_name).objects.filter(Prefix=folder_name)
    set_object_names = {obj.key for obj in objects}
    # Remove prefix
    set_object_names = {name.replace("folder_name/", "") for name in set_object_names}
    # Folders end in slash
    folder_names = {name.split("/")[1] for name in set_object_names}
    folder_names = set(folder_names) - {""}
    return folder_names


def get_folder_names_for_dropdown() -> list[dict]:
    try:
        consultation_folder_names = get_all_folder_names_within_folder(
            folder_name="app_data", bucket_name=settings.AWS_BUCKET_NAME
        )
    except RuntimeError:  # If no credentials for AWS
        consultation_folder_names = set()
    consultation_folders_formatted = [{"text": x, "value": x} for x in consultation_folder_names]
    return consultation_folders_formatted


def get_themefinder_outputs_for_question(
    question_folder_key: str, output_name: str
) -> dict | list[dict]:
    data_key = f"{question_folder_key}{output_name}.json"
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=data_key)
    return json.loads(response["Body"].read())


def import_respondent_data(consultation: ConsultationOld, respondent_data: list):
    logger.info(f"Importing respondent data for consultation: {consultation.title}")
    respondents_to_save = []
    for respondent in respondent_data:
        respondent = json.loads(respondent.decode("utf-8"))
        themefinder_respondent_id = respondent["themefinder_id"]
        # TODO - add further fields e.g. user supplied ID
        respondents_to_save.append(
            RespondentOld(
                consultation=consultation, themefinder_respondent_id=themefinder_respondent_id
            )
        )
    RespondentOld.objects.bulk_create(respondents_to_save)
    logger.info(f"Saved batch of respondents for consultation: {consultation.title}")


def import_question_part_data(consultation: ConsultationOld, question_part_dict: dict) -> QuestionPart:
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

    question, _ = QuestionOld.objects.get_or_create(
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
    corresponding_respondents = RespondentOld.objects.filter(consultation=consultation).filter(
        themefinder_respondent_id__in=themefinder_ids
    )
    respondent_dictionary = {r.themefinder_respondent_id: r for r in corresponding_respondents}

    # TODO - "response" field will change to "text", will also need to add import of options for non-free-text data
    answers = [
        Answer(
            question_part=question_part,
            respondent=respondent_dictionary[response["themefinder_id"]],
            text=response["text"],
        )
        for response in decoded_responses
    ]
    bulk_create_with_history(answers, Answer)
    logger.info(
        f"Saved batch of responses for question_number {question_part.question.number} and question part {question_part.number}"
    )


def import_themes_and_get_framework(question_part: QuestionPart, theme_data: list) -> Framework:
    logger.info(
        f"Importing themes for question_number {question_part.question.number}, part_number: {question_part.number}"
    )

    execution_run = ExecutionRun.objects.create(type=ExecutionRun.TaskType.THEME_GENERATION)
    framework = Framework.create_initial_framework(
        execution_run=execution_run, question_part=question_part
    )

    themes = [
        ThemeOld(
            framework=framework,
            name=theme["theme_name"],
            description=theme["theme_description"],
            key=theme["theme_key"],
        )
        for theme in theme_data
    ]

    ThemeOld.objects.bulk_create(themes)
    logger.info(
        f"Saved batch of themes for question_number {question_part.question.number} and question part {question_part.number}"
    )
    return framework


def import_theme_mappings(
    question_part: QuestionPart, thememapping_data: list, framework: Framework
) -> None:
    logger.info(
        f"Importing batch of theme mappings for question_number {question_part.question.number} and question part {question_part.number}"
    )
    consultation = question_part.question.consultation
    execution_run = ExecutionRun.objects.create(type=ExecutionRun.TaskType.THEME_MAPPING)

    theme_mappings = []
    for data in thememapping_data:
        data = json.loads(data.decode("utf-8"))
        themefinder_respondent_id = data["themefinder_id"]
        answer = Answer.objects.get(
            question_part=question_part,
            respondent=RespondentOld.objects.get(
                consultation=consultation, themefinder_respondent_id=themefinder_respondent_id
            ),
        )

        for theme_key in data["theme_keys"]:
            theme = ThemeOld.objects.get(framework=framework, key=theme_key)
            theme_mappings.append(
                ThemeMapping(
                    answer=answer,
                    theme=theme,
                    execution_run=execution_run,
                )
            )

    bulk_create_with_history(theme_mappings, ThemeMapping)
    logger.info(
        f"Saved batch of theme mappings for question_number {question_part.question.number} and question part {question_part.number}"
    )


def import_sentiment_mappings(question_part: QuestionPart, sentimentmapping_data: list) -> None:
    logger.info(
        f"Importing batch of sentiment mappings for question_number {question_part.question.number} and question part {question_part.number}"
    )
    consultation = question_part.question.consultation
    execution_run = ExecutionRun.objects.create(type=ExecutionRun.TaskType.SENTIMENT_ANALYSIS)

    sentiment_mappings = []
    for sentiment_mapping in sentimentmapping_data:
        sentiment_mapping = json.loads(sentiment_mapping.decode("utf-8"))
        themefinder_respondent_id = sentiment_mapping["themefinder_id"]
        answer = Answer.objects.get(
            question_part=question_part,
            respondent=RespondentOld.objects.get(
                consultation=consultation, themefinder_respondent_id=themefinder_respondent_id
            ),
        )
        sentiment_mappings.append(
            SentimentMapping(
                answer=answer,
                execution_run=execution_run,
                position=SentimentMapping.Position[sentiment_mapping["sentiment"]],
            )
        )
    bulk_create_with_history(sentiment_mappings, SentimentMapping)
    logger.info(
        f"Saved batch of sentiment mappings for question_number {question_part.question.number} and question part {question_part.number}"
    )


def import_evidence_rich_mappings(
    question_part: QuestionPart, evidence_rich_mapping_data: list
) -> None:
    logger.info(
        f"Importing batch of evidence_rich mappings for question_number {question_part.number} and question part {question_part.number}"
    )
    consultation = question_part.question.consultation
    execution_run = ExecutionRun.objects.create(type=ExecutionRun.TaskType.EVIDENCE_EVALUATION)

    evidence_rich_mappings = []
    for evidence_rich_mapping in evidence_rich_mapping_data:
        evidence_rich_mapping = json.loads(evidence_rich_mapping.decode("utf-8"))
        themefinder_respondent_id = evidence_rich_mapping["themefinder_id"]
        answer = Answer.objects.get(
            question_part=question_part,
            respondent=RespondentOld.objects.get(
                consultation=consultation, themefinder_respondent_id=themefinder_respondent_id
            ),
        )
        evidence_rich_mappings.append(
            EvidenceRichMapping(
                answer=answer,
                evidence_evaluation_execution_run=execution_run,
                evidence_rich=True if evidence_rich_mapping["evidence_rich"] == "YES" else False,
            )
        )
    bulk_create_with_history(evidence_rich_mappings, EvidenceRichMapping)
    logger.info(
        f"Saved batch of evidence rich mappings for question_number {question_part.question.number} and question part {question_part.number}"
    )


@job("default", timeout=900)
def import_respondent_data_job(consultation: ConsultationOld, respondent_data: list):
    import_respondent_data(consultation=consultation, respondent_data=respondent_data)


@job("default", timeout=900)
def import_responses_job(question_part: QuestionPart, responses_data: list):
    import_responses(question_part, responses_data)


@job("default", timeout=900)
def import_theme_mappings_job(
    question_part: QuestionPart, thememapping_data: list, framework: Framework
):
    import_theme_mappings(question_part, thememapping_data, framework)


@job("default", timeout=900)
def import_sentiment_mappings_job(question_part: QuestionPart, sentimentmapping_data: list):
    import_sentiment_mappings(question_part, sentimentmapping_data)


@job("default", timeout=900)
def import_evidence_rich_mappings_job(
    question_part: QuestionPart, evidence_rich_mapping_data: list
):
    import_evidence_rich_mappings(question_part, evidence_rich_mapping_data)


def import_all_respondents_from_jsonl(
    consultation: ConsultationOld, bucket_name: str, inputs_folder_key: str, batch_size: int
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


def import_question_part(consultation: ConsultationOld, question_part_folder_key: str) -> QuestionPart:
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


def import_themes_from_json_and_get_framework(
    question_part: QuestionPart, bucket_name: str, question_part_folder_key: str
) -> Framework:
    s3 = boto3.client("s3")
    data_key = f"{question_part_folder_key}themes.json"
    response = s3.get_object(Bucket=bucket_name, Key=data_key)
    theme_data = json.loads(response["Body"].read().decode("utf-8"))
    return import_themes_and_get_framework(question_part=question_part, theme_data=theme_data)


def import_all_theme_mappings_from_jsonl(
    question_part: QuestionPart,
    framework: Framework,
    bucket_name: str,
    question_part_folder_key: str,
    batch_size: int,
) -> None:
    logger.info(
        f"Importing theme_mappings from {question_part_folder_key}, batch_size {batch_size}"
    )
    theme_mappings_file_key = f"{question_part_folder_key}mapping.jsonl"
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=theme_mappings_file_key)
    lines = []
    for line in response["Body"].iter_lines():
        lines.append(line)
        if len(lines) == batch_size:
            import_theme_mappings_job.delay(
                question_part=question_part, thememapping_data=lines, framework=framework
            )
            lines = []
    # Any remaining lines < batch size
    if lines:
        import_theme_mappings_job.delay(
            question_part=question_part, thememapping_data=lines, framework=framework
        )


def import_all_sentiment_mappings_from_jsonl(
    question_part: QuestionPart, bucket_name: str, question_part_folder_key: str, batch_size: int
) -> None:
    logger.info(
        f"Importing sentiment mappings from {question_part_folder_key}, batch_size {batch_size}"
    )
    sentiment_mappings_file_key = f"{question_part_folder_key}sentiment.jsonl"
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=sentiment_mappings_file_key)
    lines = []
    for line in response["Body"].iter_lines():
        lines.append(line)
        if len(lines) == batch_size:
            import_sentiment_mappings_job.delay(
                question_part=question_part, sentimentmapping_data=lines
            )
            lines = []
    # Any remaining lines < batch size
    if lines:
        import_sentiment_mappings_job.delay(
            question_part=question_part, sentimentmapping_data=lines
        )


def import_all_evidence_rich_mappings_from_jsonl(
    question_part: QuestionPart, bucket_name: str, question_part_folder_key: str, batch_size: int
) -> None:
    logger.info(
        f"Importing evidence rich mappings from {question_part_folder_key}, batch_size {batch_size}"
    )
    evidence_rich_file_key = f"{question_part_folder_key}detail_detection.jsonl"
    s3_client = boto3.client("s3")
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=evidence_rich_file_key)
    except s3_client.exceptions.NoSuchKey:
        logger.info(f"No evidence rich mapping found for {question_part_folder_key}")
        return

    lines = []
    for line in response["Body"].iter_lines():
        lines.append(line)
        if len(lines) == batch_size:
            import_evidence_rich_mappings_job.delay(
                question_part=question_part, evidence_rich_mapping_data=lines
            )
            lines = []
    # Any remaining lines < batch size
    if lines:
        import_evidence_rich_mappings_job.delay(
            question_part=question_part, evidence_rich_mapping_data=lines
        )
