import random

import factory
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
    name = factory.LazyAttribute(lambda o: fake.sentence())
    description = factory.LazyAttribute(lambda o: fake.paragraph())


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
