import random
from typing import Optional

import factory
import yaml
from factory.django import DjangoModelFactory
from faker import Faker

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models

fake = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda o: fake.email())
    is_staff = False
    password = factory.LazyAttribute(lambda o: fake.password())


class Consultation2Factory(DjangoModelFactory):
    class Meta:
        model = models.Consultation2

    text = factory.LazyAttribute(lambda o: fake.sentence())
    users = factory.RelatedFactoryList(UserFactory, factory_related_name="consultation", size=3)


class Question2Factory(DjangoModelFactory):
    class Meta:
        model = models.Question2

    text = factory.LazyAttribute(lambda o: fake.sentence())
    consultation = factory.SubFactory(Consultation2Factory)
    order = factory.LazyAttribute(lambda n: random.randint(1, 10))


# TODO -  all free-text for now, can add to this in future
class QuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(Question2Factory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.FREE_TEXT


class RespondentFactory(DjangoModelFactory):
    class Meta:
        model = models.Respondent

    consultation = factory.SubFactory(Consultation2Factory)


class Answer2Factory(DjangoModelFactory):
    class Meta:
        model = models.Answer2

    question_part = factory.SubFactory(QuestionPartFactory)
    respondent = factory.SubFactory(RespondentFactory)
    text = factory.LazyAttribute(lambda o: fake.paragraph())


class ExecutionRunFactory(DjangoModelFactory):
    class Meta:
        model = models.ExecutionRun

    type = factory.Iterator(models.ExecutionRun.TaskType.values)


class FrameworkFactory(DjangoModelFactory):
    class Meta:
        model = models.Framework

    execution_run = factory.SubFactory(ExecutionRunFactory)
    question_part = factory.SubFactory(QuestionPartFactory)
    change_reason = factory.LazyAttribute(lambda o: fake.sentence())
    user = factory.SubFactory(UserFactory)
    precursor = None  # TODO - add option for framework


class Theme2Factory(DjangoModelFactory):
    class Meta:
        model = models.Theme2

    framework = factory.SubFactory(FrameworkFactory)
    precursor = None  # TODO - add option for theme
    theme_name = factory.LazyAttribute(lambda o: fake.sentence())
    theme_description = factory.LazyAttribute(lambda o: fake.paragraph())


class ThemeMappingFactory(DjangoModelFactory):
    class Meta:
        model = models.ThemeMapping

    answer = factory.SubFactory(Answer2Factory)
    theme = factory.SubFactory(Theme2Factory)
    reason = factory.LazyAttribute(lambda o: fake.sentence())
    execution_run = factory.SubFactory(ExecutionRunFactory)


class SentimentMappingFactory(DjangoModelFactory):
    class Meta:
        model = models.SentimentMapping

    answer = factory.SubFactory(Answer2Factory)
    execution_run = factory.SubFactory(ExecutionRunFactory)
    position = factory.Iterator(models.SentimentMapping.PositionType.values)


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
