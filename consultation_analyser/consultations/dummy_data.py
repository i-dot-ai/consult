import json
import logging
import random
from typing import Optional

import yaml
from django_rq import job

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    ThemeFactory,
)
from consultation_analyser.hosting_environment import HostingEnvironment

logger = logging.getLogger("dummy_data")


def create_dummy_consultation_from_yaml(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[models.Consultation] = None,
) -> ConsultationFactory:
    """
    Create consultation with questions, responses and themes from yaml file.
    Creates relevant objects: Consultation, Question, Response, Theme, ResponseAnnotation,
    Respondent.
    """
    if HostingEnvironment.is_production():
        raise RuntimeError("Dummy data generation should not be run in production")

    if not consultation:
        consultation = ConsultationFactory(title="Dummy Consultation")

    respondents = [
        RespondentFactory(consultation=consultation, themefinder_id=i + 1)
        for i in range(number_respondents)
    ]
    logger.info(f"Created {number_respondents} respondents")

    with open(file_path, "r") as file:
        questions_data = yaml.safe_load(file)

    # Save all questions, and corresponding question parts and answers
    for question_data in questions_data:
        logger.info("Creating a new question...")
        has_free_text = question_data["has_free_text"]
        has_multiple_choice = question_data["has_multiple_choice"]

        if has_multiple_choice:
            options = json.loads(json.dumps(question_data.get("multiple_choice_options")))
        else:
            options = None

        question = QuestionFactory(
            text=question_data["question_text"],
            number=question_data["number"],
            consultation=consultation,
            has_free_text=has_free_text,
            has_multiple_choice=has_multiple_choice,
            multiple_choice_options=options,
        )

        if has_free_text:
            logger.info("Free text question - create themes")
            theme_objects = []
            themes_data = question_data["themes"]
            for data in themes_data:
                theme_name = data["name"]
                theme_desc = data["description"]
                theme_key = data["key"]
                theme_obj = ThemeFactory(
                    question=question, description=theme_desc, key=theme_key, name=theme_name
                )
                theme_objects.append(theme_obj)

        # For each respondent add random response and themes
        for respondent in respondents:
            logger.info("Add responses")
            response = ResponseFactory(
                question=question, free_text="i am a answer", respondent=respondent
            )

            if has_free_text:
                response.free_text = random.choice(question_data.get("free_text_answers", [""]))
                response.save()
                themes_for_response = random.sample(
                    theme_objects, k=random.randint(1, len(theme_objects))
                )
                random_sentiment = random.choice(
                    [s[0] for s in models.ResponseAnnotation.Sentiment.choices]
                )
                random_evidence_rich = random.choice(
                    [e[0] for e in models.ResponseAnnotation.EvidenceRich.choices]
                )
                response_annotation = ResponseAnnotationFactoryNoThemes(
                    response=response,
                    sentiment=random_sentiment,
                    evidence_rich=random_evidence_rich,
                )
                response_annotation.add_original_ai_themes(themes_for_response)
                # Haven't considered human changes to themes, just AI generated

            if has_multiple_choice:
                logger.info("Add multiple choice responses")
                chosen_options = random.sample(
                    question_data["multiple_choice_options"],
                    k=random.randint(1, len(question_data["multiple_choice_options"])),
                )
                response.chosen_options = chosen_options
                response.save()
        logger.info(f"Finished adding question and responses for question {question.number}")
        models.DemographicOption.rebuild_for_consultation(consultation=consultation)
        logger.info(f"Finished adding dummy data for consultation {consultation.slug}")
    return consultation


# Will only be run occasionally to create dummy data - not in prod
@job("default", timeout=2400)
def create_dummy_consultation_from_yaml_job(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[models.Consultation] = None,
):
    create_dummy_consultation_from_yaml(
        file_path=file_path,
        number_respondents=number_respondents,
        consultation=consultation,
    )
