import random
from typing import Literal, Optional

import yaml
from django.conf import settings
from django_rq import job

from backend.consultations.models import (
    Consultation,
    MultiChoiceAnswer,
    Question, Response,
)
from backend.factories import (
    CandidateThemeFactory,
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    SelectedThemeFactory,
)
from backend.hosting_environment import HostingEnvironment

logger = settings.LOGGER

DATA_BY_STAGE = {
    Consultation.Stage.ANALYSIS: {
        "CONSULTATION_NAME": "Dummy Consultation at Analysis Stage",
        "QUESTION_THEME_STATUS": Question.ThemeStatus.CONFIRMED,
    },
    Consultation.Stage.THEME_SIGN_OFF: {
        "CONSULTATION_NAME": "Dummy Consultation at Theme Sign Off Stage",
        "QUESTION_THEME_STATUS": Question.ThemeStatus.DRAFT,
    },
}


def create_consultation(stage):
    """Create and return a Consultation."""
    name = DATA_BY_STAGE[stage]["CONSULTATION_NAME"]
    return ConsultationFactory(title=name, stage=stage)


def create_respondents(consultation, number_respondents):
    """Create and return a list of Respondents."""
    return [
        RespondentFactory(consultation=consultation, themefinder_id=i)
        for i in range(1, number_respondents + 1)
    ]


def create_question(consultation, question_data):
    """Create and return a Question."""
    has_free_text = question_data["has_free_text"]
    has_multiple_choice = question_data["has_multiple_choice"]
    theme_status = DATA_BY_STAGE[consultation.stage]["QUESTION_THEME_STATUS"]

    return QuestionFactory(
        text=question_data["question_text"],
        number=question_data["number"],
        consultation=consultation,
        has_free_text=has_free_text,
        has_multiple_choice=has_multiple_choice,
        theme_status=theme_status,
    )


def create_multi_choice_answers(question, choices):
    """Create MultiChoiceAnswers for a multiple choice question."""
    multi_choice_objects = [MultiChoiceAnswer(question=question, text=choice) for choice in choices]
    MultiChoiceAnswer.objects.bulk_create(multi_choice_objects)


def create_candidate_theme_recursive(
    question, number_respondents, candidate_theme_data, parent=None
):
    """Create a CandidateTheme (and SelectedTheme if selected) recursively."""
    name = candidate_theme_data.get("name")
    description = candidate_theme_data.get("description", "")
    key = candidate_theme_data.get("key")
    approximate_frequency = round(
        candidate_theme_data.get("approximate_frequency_pct", 0) * number_respondents
    )

    candidate_theme = CandidateThemeFactory(
        question=question,
        description=description,
        name=name,
        parent=parent,
        approximate_frequency=approximate_frequency,
    )

    if question.theme_status == Question.ThemeStatus.CONFIRMED and candidate_theme_data.get(
        "selected"
    ):
        selected_theme = SelectedThemeFactory(
            question=question, name=name, description=description, key=key
        )
        candidate_theme.selectedtheme = selected_theme
        candidate_theme.save()

    for child in candidate_theme_data.get("children", []):
        create_candidate_theme_recursive(
            question, number_respondents, child, parent=candidate_theme
        )


def create_response(respondent, question, free_text_answers):
    """Create and return a Response."""
    free_text = random.choice(free_text_answers) if question.has_free_text else None
    return ResponseFactory(question=question, free_text=free_text, respondent=respondent)


def create_response_annotation(response, question):
    """Create a ResponseAnnotation and ResponseAnnotationThemes for a free text response."""
    selected_themes = list(question.selectedtheme_set.all())
    themes_for_response = random.sample(
        selected_themes,
        k=random.randint(1, len(selected_themes)),
    )
    random_sentiment = random.choice([s[0] for s in Response.Sentiment.choices])
    random_evidence_rich = random.choice([True, False])
    response.sentiment=random_sentiment
    response.evidence_rich=random_evidence_rich
    response.add_original_ai_themes(themes_for_response)
    response.save()


def create_response_chosen_options(response, multiple_choice_options):
    """Add chosen options to a multiple choice response."""
    chosen_options = random.sample(
        multiple_choice_options,
        k=random.randint(1, len(multiple_choice_options)),
    )
    answers = MultiChoiceAnswer.objects.filter(question=response.question, text__in=chosen_options)
    response.chosen_options.add(*answers)


def create_dummy_consultation_from_yaml(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[Consultation] = None,
    consultation_stage: Optional[Literal["theme_sign_off", "analysis"]] = None,
) -> ConsultationFactory:
    """
    Create consultation with questions, responses and themes from yaml file.
    Creates relevant objects: Consultation, Question, CandidateTheme, SelectedTheme,
    Response, ResponseAnnotation, Respondent.
    """
    if HostingEnvironment.is_production():
        raise RuntimeError("Dummy data generation should not be run in production")

    consultation_stage = consultation_stage or "analysis"
    if consultation is None:
        logger.info("Creating consultation at stage: {stage}", stage=consultation_stage)
        consultation = create_consultation(consultation_stage)

    logger.info("Creating {number_respondents} respondents", number_respondents=number_respondents)
    respondents = create_respondents(consultation, number_respondents)

    with open(file_path, "r") as file:
        questions_data = yaml.safe_load(file)

    for question_data in questions_data:
        logger.info("Creating a new question...")
        question = create_question(consultation, question_data)
        multiple_choice_options = question_data.get("multiple_choice_options", [])
        free_text_answers = question_data.get("free_text_answers", [])

        if question.has_multiple_choice:
            logger.info("Multiple choice question - create multi choice answers")
            create_multi_choice_answers(question, multiple_choice_options)

        if question.has_free_text:
            logger.info("Free text question - create candidate themes")

            for candidate_theme_data in question_data["candidate_themes"]:
                create_candidate_theme_recursive(question, len(respondents), candidate_theme_data)

        for respondent in respondents:
            logger.info("Creating a new response...")
            response = create_response(respondent, question, free_text_answers)

            if question.has_free_text and consultation.stage == Consultation.Stage.ANALYSIS:
                logger.info("Free text question - create response annotation")
                create_response_annotation(response, question)

            if question.has_multiple_choice:
                logger.info("Multiple choice question - create response chosen options")
                create_response_chosen_options(response, multiple_choice_options)

        logger.info(
            "Finished adding question and responses for question {question_number}",
            question_number=question.number,
        )
        logger.info(
            "Finished adding dummy data for consultation {consultation_code}",
            consultation_code=consultation.code,
        )
    return consultation


# Will only be run occasionally to create dummy data - not in prod
@job("default", timeout=2400)
def create_dummy_consultation_from_yaml_job(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[Consultation] = None,
):
    create_dummy_consultation_from_yaml(
        file_path=file_path,
        number_respondents=number_respondents,
        consultation=consultation,
    )
