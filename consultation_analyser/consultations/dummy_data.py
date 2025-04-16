import json
import logging
import math
import random
from typing import Optional

import django
import yaml
from django_rq import job

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    ConsultationFactory,
    ExecutionRunFactory,
    FreeTextAnswerFactory,
    FreeTextQuestionPartFactory,
    InitialFrameworkFactory,
    InitialThemeFactory,
    MultipleOptionAnswerFactory,
    MultipleOptionQuestionPartFactory,
    QuestionFactory,
    RespondentFactory,
    SentimentMappingFactory,
    SingleOptionAnswerFactory,
    SingleOptionQuestionPartFactory,
    ThemeMappingFactory,
)
from consultation_analyser.hosting_environment import HostingEnvironment

logger = logging.getLogger("dummy_data")


def simulate_user_amending_themes(question_part: models.QuestionPart):
    logger.info(
        f"Starting amending themes for question number {question_part.question.number} and question part number {question_part.number}"
    )
    # Ideally random using .order_by("?") but might take too long
    latest_theme_mappings = models.ThemeMapping.get_latest_theme_mappings(
        question_part=question_part
    )
    total = latest_theme_mappings.count()
    latest_framework = (
        models.Framework.objects.filter(question_part=question_part).order_by("created_at").last()
    )
    latest_themes = models.Theme.objects.filter(framework=latest_framework)
    all_responses = models.Answer.objects.filter(question_part=question_part)

    # Delete some theme mappings
    sample_size = math.floor(total / 5)
    random_sample_ids = latest_theme_mappings[:sample_size].values_list("id", flat=True)
    latest_theme_mappings.filter(id__in=random_sample_ids).delete()

    # Now select some responses and add new themes
    sample_size = math.floor(total / 5)

    chosen_responses = all_responses[:sample_size]
    for response in chosen_responses:
        try:
            random_theme = latest_themes.order_by("?")[0]
            ThemeMappingFactory(theme=random_theme, answer=response)
        except django.db.utils.IntegrityError:
            # will sometimes get uniqueness constraint errors
            pass

    # Now update all theme mappings and responses to mark as user reviewed
    theme_mappings = models.ThemeMapping.get_latest_theme_mappings(question_part=question_part)
    total = theme_mappings.count()
    theme_mappings.update(user_audited=True)
    logger.info(
        f"Simulated amending themes for question number {question_part.question.number} and question part number {question_part.number}"
    )


def create_dummy_consultation_from_yaml(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[models.Consultation] = None,
    include_changes_to_themes: bool = False,
) -> ConsultationFactory:
    """
    Create consultation with question, question parts, answers and themes from yaml file.
    Creates relevant objects: Consultation, Question, QuestionPart, Answer, Theme, ThemeMapping,
    SentimentMapping, Framework, ExecutionRun.
    """
    if HostingEnvironment.is_production():
        raise RuntimeError("Dummy data generation should not be run in production")

    if not consultation:
        consultation = ConsultationFactory()

    respondents = [
        RespondentFactory(consultation=consultation, themefinder_respondent_id=i + 1)
        for i in range(number_respondents)
    ]
    logger.info(f"Created {number_respondents} respondents")

    with open(file_path, "r") as file:
        questions_data = yaml.safe_load(file)

    # Save all questions, and corresponding question parts and answers
    for question_data in questions_data:
        question = QuestionFactory(
            text=question_data["question_text"],
            number=question_data["number"],
            consultation=consultation,
        )
        parts = question_data["parts"]

        # Each question part is considered separately
        for part in parts:
            question_part_type = part["type"]
            if question_part_type == models.QuestionPart.QuestionType.FREE_TEXT:
                question_part = FreeTextQuestionPartFactory(
                    question=question,
                    text=part["text"],
                    type=question_part_type,
                    number=part["number"],
                )
                logger.info(
                    f"Created question part for question number {question.number} and question part number {question_part.number}"
                )

                # Simulate execution runs for each question to generate themes, theme mapping
                sentiment_mapping_run = ExecutionRunFactory(
                    type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
                )
                theme_generation_run = ExecutionRunFactory(
                    type=models.ExecutionRun.TaskType.THEME_GENERATION
                )
                framework = InitialFrameworkFactory(
                    execution_run=theme_generation_run, question_part=question_part
                )
                theme_mapping_run = ExecutionRunFactory(
                    type=models.ExecutionRun.TaskType.THEME_MAPPING
                )
                themes = part.get("themes", [])
                theme_objects = [
                    InitialThemeFactory(
                        framework=framework,
                        name=theme["name"],
                        description=theme["description"],
                        key=theme["key"],
                    )
                    for theme in themes
                ]

            elif question_part_type == models.QuestionPart.QuestionType.SINGLE_OPTION:
                question_part = SingleOptionQuestionPartFactory(
                    question=question,
                    text=part["text"],
                    type=question_part_type,
                    options=json.loads(json.dumps(part.get("options"))),
                    number=part["number"],
                )
            else:
                question_part = MultipleOptionQuestionPartFactory(
                    question=question,
                    text=part["text"],
                    type=question_part_type,
                    options=json.loads(json.dumps(part.get("options"))),
                    number=part["number"],
                )

            logger.info(
                f"Finished creating themes, execution runs etc for question number {question.number} and question part number {question_part.number}"
            )

            # Now populate the answers and corresponding themes etc. for these question parts
            for respondent in respondents:
                logger.info(
                    f"Start populating responses for question number {question.number} and question part number {question_part.number}"
                )

                if question_part_type == models.QuestionPart.QuestionType.FREE_TEXT:
                    text = random.choice(part.get("free_text_answers", [""]))
                    answer = FreeTextAnswerFactory(
                        question_part=question_part, text=text, respondent=respondent
                    )
                elif question_part_type == models.QuestionPart.QuestionType.SINGLE_OPTION:
                    chosen_option = random.choice(part["options"])
                    chosen_options = [chosen_option]
                    text = ""
                    answer = SingleOptionAnswerFactory(
                        question_part=question_part,
                        text=text,
                        chosen_options=chosen_options,
                        respondent=respondent,
                    )
                else:
                    chosen_options = random.sample(
                        part["options"], k=random.randint(1, len(part["options"]))
                    )
                    text = ""
                    answer = MultipleOptionAnswerFactory(
                        question_part=question_part,
                        text=text,
                        chosen_options=chosen_options,
                        respondent=respondent,
                    )
                    # Also add sentiment to answer replicating the sentiment mapping step
                    # This is agree/disagree/unclear
                    SentimentMappingFactory(answer=answer, execution_run=sentiment_mapping_run)
                    logger.info(
                        f"Finished populating responses for question number {question.number} and question part number {question_part.number}"
                    )

                # Now map (multiple) themes to each answer for free-text questions.
                # This is in a different order to how it would work in pipeline - but this is as we
                # are reading from file.
                if question_part_type == models.QuestionPart.QuestionType.FREE_TEXT:
                    themes_for_answer = random.sample(
                        theme_objects, k=random.randint(1, len(theme_objects))
                    )
                    for theme in themes_for_answer:
                        ThemeMappingFactory(
                            answer=answer, theme=theme, execution_run=theme_mapping_run
                        )
                    logger.info(
                        f"Added theme mappings for question number {question.number} and question part number {question_part.number}"
                    )
                    if include_changes_to_themes:
                        simulate_user_amending_themes(question_part)

    return consultation


# Will only be run occasionally to create dummy data
# Not in prod
@job("default", timeout=1800)
def create_dummy_consultation_from_yaml_job(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[models.Consultation] = None,
    include_changes_to_themes: bool = False,
):
    create_dummy_consultation_from_yaml(
        file_path=file_path,
        number_respondents=number_respondents,
        consultation=consultation,
        include_changes_to_themes=include_changes_to_themes,
    )
