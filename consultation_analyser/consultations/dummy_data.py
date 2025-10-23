import json
import random
from typing import Any, Optional

import yaml
from django.conf import settings
from django_rq import job

from consultation_analyser.consultations import models
from consultation_analyser.consultations.models import MultiChoiceAnswer
from consultation_analyser.factories import (
    CandidateThemeFactory,
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    SelectedThemeFactory,
)
from consultation_analyser.hosting_environment import HostingEnvironment

logger = settings.LOGGER


def create_dummy_consultation_from_yaml(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[models.Consultation] = None,
    consultation_stage: Any[models.Consultation.Stage] = models.Consultation.Stage.ANALYSIS,
) -> ConsultationFactory:
    """
    Create consultation with questions, responses and themes from yaml file.
    Creates relevant objects: Consultation, Question, CandidateTheme, SelectedTheme,
    Response, ResponseAnnotation, Respondent.
    """
    if HostingEnvironment.is_production():
        raise RuntimeError("Dummy data generation should not be run in production")

    if not consultation:
        name = (
            "Dummy Consultation at Analysis Stage"
            if consultation_stage == models.Consultation.Stage.ANALYSIS
            else "Dummy Consultation at Theme Sign Off Stage"
        )
        consultation = ConsultationFactory(title=name, stage=consultation_stage)

    respondents = [
        RespondentFactory(consultation=consultation, themefinder_id=i + 1)
        for i in range(number_respondents)
    ]
    logger.info("Created {number_respondents} respondents", number_respondents=number_respondents)

    with open(file_path, "r") as file:
        questions_data = yaml.safe_load(file)

    is_analysis_stage = consultation.stage == models.Consultation.Stage.ANALYSIS

    # Save all questions, and corresponding question parts and answers
    for question_data in questions_data:
        logger.info("Creating a new question...")
        has_free_text = question_data["has_free_text"]
        has_multiple_choice = question_data["has_multiple_choice"]
        theme_status = (
            models.Question.ThemeStatus.CONFIRMED
            if is_analysis_stage
            else models.Question.ThemeStatus.DRAFT
        )
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
            theme_status=theme_status,
        )
        for option in options or []:
            MultiChoiceAnswer(question=question, text=option).save()

        if has_free_text:
            logger.info("Free text question - create themes")

            def _create_candidate_theme_recursive(data, parent=None):
                """Create a CandidateTheme (and SelectedTheme if selected) and recurse into children.

                Returns the created CandidateTheme instance.
                """
                name = data.get("name")
                description = data.get("description", "")
                key = data.get("key")

                candidate = CandidateThemeFactory(
                    question=question, description=description, name=name, parent=parent
                )

                if is_analysis_stage and data.get("selected"):
                    selected_theme = SelectedThemeFactory(
                        question=question, name=name, description=description, key=key
                    )
                    candidate.selectedtheme = selected_theme
                    candidate.save()

                for child in data.get("children", []):
                    _create_candidate_theme_recursive(child, parent=candidate)

                return candidate

            for candidate_theme_data in question_data.get("candidate_themes", []):
                _create_candidate_theme_recursive(candidate_theme_data)

        # For each respondent add random response and themes
        for respondent in respondents:
            logger.info("Add responses")
            response = ResponseFactory(
                question=question, free_text="i am a answer", respondent=respondent
            )

            if has_free_text:
                response.free_text = random.choice(question_data.get("free_text_answers", [""]))
                response.save()

                if is_analysis_stage:
                    logger.info("Add response annotations with themes")
                    selected_themes = list(question.selectedtheme_set.all())
                    themes_for_response = random.sample(
                        selected_themes,
                        k=random.randint(1, len(selected_themes)),
                    )
                    random_sentiment = random.choice(
                        [s[0] for s in models.ResponseAnnotation.Sentiment.choices]
                    )
                    random_evidence_rich = random.choice([True, False])
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
                for answer in MultiChoiceAnswer.objects.filter(text__in=chosen_options):
                    response.chosen_options.add(answer)
                response.save()

        logger.info(
            "Finished adding question and responses for question {question_number}",
            question_number=question.number,
        )
        logger.info(
            "Finished adding dummy data for consultation {consultation_slug}",
            consultation_slug=consultation.slug,
        )
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
