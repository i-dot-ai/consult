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


class QuestionGroupFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionGroup


class Question2Factory(DjangoModelFactory):
    class Meta:
        model = models.Question2

    text = factory.LazyAttribute(lambda o: fake.sentence())
    consultation = factory.SubFactory(Consultation2Factory)
    order = factory.LazyAttribute(lambda n: random.randint(1, 10))
    question_group = None


# TODO -  all free-text for now, can add to this in future
class QuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(Question2Factory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.FREE_TEXT


class ExpandedQuestionFactory(DjangoModelFactory):
    class Meta:
        model = models.ExpandedQuestion

    question_part = factory.SubFactory(QuestionPartFactory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    # TODO - actually the text probably comes from the question part and question


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

    xecution_run = factory.SubFactory(ExecutionRunFactory)
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


def create_consultation_from_yaml(
    file_path: str = "./tests/examples/sample_questions.yml",
    number_respondents: int = 5,
    consultation: Optional[models.Consultation2] = None,
) -> Consultation2Factory:
    """Create consultation with question, question parts and answers from yaml file."""
    if not consultation:
        consultation = Consultation2Factory()
    respondents = [RespondentFactory(consultation=consultation) for _ in range(number_respondents)]

    with open(file_path, "r") as file:
        questions_data = yaml.safe_load(file)

    # Save all questions, and corresponding question parts and answers
    for question_data in questions_data:
        question_text = question_data["question_text"]
        order = question_data["order"]
        parts = (
            question_data["part"]
            if isinstance(question_data["part"], list)
            else [question_data["part"]]
        )
        question = Question2Factory(text=question_text, order=order, consultation=consultation)

        for part in parts:
            question_part = QuestionPartFactory(
                question=question,
                text=part["text"],
                type=part["type"],
                options=part.get("options", []),
                order=part["order"],
            )

            # Generate answers for each respondent
            for respondent in respondents:
                if part["type"] == "single_option":
                    chosen_options = random.choice(part["options"])
                    text = ""
                elif part["type"] == "multiple_option":
                    chosen_options = random.sample(
                        part["options"], k=random.randint(1, len(part["options"]))
                    )
                    text = ""
                elif part["type"] == "free_text":
                    text = random.choice(part.get("free_text_answers", [""]))
                    chosen_options = []

                Answer2Factory(
                    question_part=question_part,
                    text=text,
                    chosen_options=chosen_options,
                    respondent=respondent,
                )
    return consultation
