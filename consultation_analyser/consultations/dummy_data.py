import json
import random
from typing import Optional

import yaml

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


def create_dummy_consultation_from_yaml(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[models.Consultation] = None,
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

                # Simulate execution runs for each question to generate themes, theme mapping
                sentiment_mapping_run = ExecutionRunFactory(
                    type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
                )
                theme_generation_run = ExecutionRunFactory(
                    type=models.ExecutionRun.TaskType.THEME_GENERATION
                )
                framework = InitialFrameworkFactory(
                    theme_generation_execution_run=theme_generation_run, question_part=question_part
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

            # Now populate the answers and corresponding themes etc. for these question parts
            for respondent in respondents:
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
                    SentimentMappingFactory(
                        answer=answer, sentiment_analysis_execution_run=sentiment_mapping_run
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
                            answer=answer,
                            theme=theme,
                            theme_mapping_execution_run=theme_mapping_run,
                        )

    return consultation
