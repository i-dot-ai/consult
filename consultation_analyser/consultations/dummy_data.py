import random
from typing import Optional

import yaml

from consultation_analyser.consultations import models
from consultation_analyser.factories2 import (
    Answer2Factory,
    Consultation2Factory,
    ExecutionRunFactory,
    FrameworkFactory,
    Question2Factory,
    QuestionPartFactory,
    RespondentFactory,
    SentimentMappingFactory,
    Theme2Factory,
    ThemeMappingFactory,
)
from consultation_analyser.hosting_environment import HostingEnvironment


def create_dummy_consultation_from_yaml(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 10,
    consultation: Optional[models.Consultation2] = None,
) -> Consultation2Factory:
    """
    Create consultation with question, question parts, answers and themes from yaml file.
    Creates relevant objects: Consultation, Question, QuestionPart, Answer, Theme, ThemeMapping,
    SentimentMapping, Framework, ExecutionRun.
    """
    if HostingEnvironment.is_production():
        raise RuntimeError("Dummy data generation should not be run in production")

    if not consultation:
        consultation = Consultation2Factory()
    respondents = [RespondentFactory(consultation=consultation) for _ in range(number_respondents)]

    with open(file_path, "r") as file:
        questions_data = yaml.safe_load(file)

    # Save all questions, and corresponding question parts and answers
    for question_data in questions_data:
        question = Question2Factory(
            text=question_data["question_text"],
            order=question_data["order"],
            consultation=consultation,
        )
        parts = question_data["parts"]

        # Each question part is considered separately
        for part in parts:
            question_part_type = part["type"]
            question_part = QuestionPartFactory(
                question=question,
                text=part["text"],
                type=question_part_type,
                options=part.get("options", []),
                order=part["order"],
            )

            # Get themes if free_text
            if question_part_type == models.QuestionPart.QuestionType.FREE_TEXT:
                # Simulate execution runs for each question to generate sentiment, themes, theme mapping
                sentiment_run = ExecutionRunFactory(
                    type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
                )
                theme_generation_run = ExecutionRunFactory(
                    type=models.ExecutionRun.TaskType.THEME_GENERATION
                )
                framework = FrameworkFactory(
                    execution_run=theme_generation_run, question_part=question_part
                )
                theme_mapping_run = ExecutionRunFactory(
                    type=models.ExecutionRun.TaskType.THEME_MAPPING
                )
                themes = part.get("themes", [])
                for theme in themes:
                    theme_objects = [
                        Theme2Factory(
                            framework=framework,
                            theme_name=theme["name"],
                            theme_description=theme["description"],
                        )
                    ]

            # Now populate the answers and corresponding themes etc. for these question parts
            for respondent in respondents:
                if question_part_type == models.QuestionPart.QuestionType.SINGLE_OPTION:
                    chosen_options = random.choice(part["options"])
                    text = ""
                elif question_part_type == models.QuestionPart.QuestionType.MULTIPLE_OPTIONS:
                    chosen_options = random.sample(
                        part["options"], k=random.randint(1, len(part["options"]))
                    )
                    text = ""
                elif question_part_type == models.QuestionPart.QuestionType.FREE_TEXT:
                    text = random.choice(part.get("free_text_answers", [""]))
                    chosen_options = []

                answer = Answer2Factory(
                    question_part=question_part,
                    text=text,
                    chosen_options=chosen_options,
                    respondent=respondent,
                )
                # Now map (multiple) themes and sentiment to each answer for free-text questions.
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
                    sentiment = random.choice(models.SentimentMapping.PositionType.values)
                    SentimentMappingFactory(
                        answer=answer, execution_run=sentiment_run, position=sentiment
                    )

    return consultation
