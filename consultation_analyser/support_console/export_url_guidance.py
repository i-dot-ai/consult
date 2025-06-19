import io
import logging

import boto3
import pandas as pd
from django.conf import settings

from consultation_analyser.consultations.models import ConsultationOld, QuestionPart, RespondentOld

logger = logging.getLogger("export")
s3 = boto3.client("s3")


def get_response_id_mapping(s3_key: str, file_name: str) -> dict:
    # Get the response ID mapping
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=f"{s3_key}/{file_name}")
    answer_df = pd.read_excel(response["Body"].read(), sheet_name="Sheet2")

    return answer_df["Response ID"].to_dict()


def get_key_for_question_part(question_part: QuestionPart) -> str:
    return f"Question {question_part.question.number}: {question_part.text}"


def get_urls_for_respondent(
    respondent: RespondentOld, consultation: ConsultationOld, base_url: str
) -> dict:
    urls = {}

    # Not all respondents have answered all questions, but we should provide a string for each question for the xlsx export formatting
    for question_part in QuestionPart.objects.filter(question__consultation=consultation):
        urls[get_key_for_question_part(question_part)] = ""

    for answer in respondent.answer_set.all():
        urls[get_key_for_question_part(answer.question_part)] = (
            f"{base_url}consultations/{consultation.slug}/responses/{answer.question_part.question.slug}/{answer.id}/"
        )
    return urls


def get_urls_for_consultation(
    consultation: ConsultationOld,
    base_url: str,
    s3_key: str,
    file_name: str,
) -> pd.DataFrame:
    response_id_mapping = get_response_id_mapping(s3_key, file_name)

    data = []

    for id, respondent_key in response_id_mapping.items():
        try:
            logger.info(f"Processing respondent {id}")
            respondent = RespondentOld.objects.get(
                consultation=consultation, themefinder_respondent_id=id
            )
            respondent_data = {
                "Original ID": respondent_key,
                "Website ID": id,
            }

            respondent_data = respondent_data | get_urls_for_respondent(
                respondent, consultation, base_url
            )

            data.append(respondent_data)
        except RespondentOld.DoesNotExist:
            logger.info(f"Respondent with themefinder_response_id {id} does not exist")

    with io.BytesIO() as output:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pd.DataFrame.from_dict(data).to_excel(writer, index=False)
        file_data = output.getvalue()

        s3.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=f"{s3_key}/url_mappings.xlsx",
            Body=file_data,
        )

    return
