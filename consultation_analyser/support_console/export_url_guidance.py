import logging

import pandas as pd

from consultation_analyser.consultations.models import QuestionPart, Respondent

logger = logging.getLogger("export")


def get_response_id_mapping():
    # Get the response ID mapping

    # TODO: import from S3
    xls = pd.ExcelFile("downloads/Consultation Data Extract.xlsx")
    df = pd.read_excel(xls, "Sheet2")

    return df["Response ID"].to_dict()


def get_key_for_question_part(question_part):
    return f"Question {question_part.question.number}: {question_part.text}"


def get_urls_for_respondent(respondent, consultation, base_url):
    urls = {}

    # Not all respondents have answered all questions, but we should provide a string for each question for the xlsx export formatting
    for question_part in QuestionPart.objects.filter(question__consultation=consultation):
        urls[get_key_for_question_part(question_part)] = ""

    for answer in respondent.answer_set.all():
        urls[get_key_for_question_part(answer.question_part)] = (
            f"{base_url}consultations/{consultation.slug}/responses/{answer.question_part.question.slug}/{answer.id}/"
        )
    return urls


def get_urls_for_consultation(consultation, base_url):
    response_id_mapping = get_response_id_mapping()

    data = []

    for id, respondent_key in response_id_mapping.items():
        try:
            logger.info(f"Processing respondent {id}")
            respondent = Respondent.objects.get(
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
        except Respondent.DoesNotExist:
            logger.error(f"Respondent with themefinder_response_id {id} does not exist")

    return pd.DataFrame.from_dict(data)
