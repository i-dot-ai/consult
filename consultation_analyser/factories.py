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


class ConsultationFactory(DjangoModelFactory):
    class Meta:
        model = models.Consultation

    text = factory.LazyAttribute(lambda o: fake.sentence())


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = models.Question

    text = factory.LazyAttribute(lambda o: fake.sentence())
    consultation = factory.SubFactory(ConsultationFactory)
    order = factory.LazyAttribute(lambda n: random.randint(1, 10))


# TODO -  all free-text for now, can add to this in future
class QuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(QuestionFactory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.FREE_TEXT


class RespondentFactory(DjangoModelFactory):
    class Meta:
        model = models.Respondent

    consultation = factory.SubFactory(ConsultationFactory)


class AnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.Answer

    question_part = factory.SubFactory(QuestionPartFactory)
    respondent = factory.SubFactory(RespondentFactory)
    text = factory.LazyAttribute(lambda o: fake.paragraph())


class ExecutionRunFactory(DjangoModelFactory):
    class Meta:
        model = models.ExecutionRun

    type = factory.Iterator(models.ExecutionRun.TaskType.values)


class InitialFrameworkFactory(DjangoModelFactory):
    # Creates an initial framework
    class Meta:
        model = models.Framework

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        execution_run = kwargs.get("execution_run")
        question_part = kwargs.get("question_part")
        if not execution_run:
            execution_run = ExecutionRunFactory()
        if not question_part:
            question_part = QuestionPartFactory()
        return model_class.create_initial_framework(
            execution_run=execution_run, question_part=question_part
        )


class DescendantFrameworkFactory(DjangoModelFactory):
    # Creates a framework that is is derived from another framework
    class Meta:
        model = models.Framework

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        precursor = kwargs.get("precursor")
        user = kwargs.get("user")
        change_reason = kwargs.get("change_reason")
        if not precursor:
            precursor = InitialFrameworkFactory()
        if not user:
            user = UserFactory()
        if not change_reason:
            change_reason = fake.sentence()
        return precursor.create_descendant_framework(user=user, change_reason=change_reason)


class InitialThemeFactory(DjangoModelFactory):
    # Create an initial theme (which will have come from the theme generation task)
    class Meta:
        model = models.Theme

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        framework = kwargs.get("framework")
        name = kwargs.get("name")
        description = kwargs.get("description")
        if not framework:
            framework = InitialFrameworkFactory()
        if not name:
            name = fake.sentence()
        if not description:
            description = fake.paragraph()
        return model_class.create_initial_theme(
            framework=framework, name=name, description=description
        )


class DescendantThemeFactory(DjangoModelFactory):
    class Meta:
        model = models.Theme

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        precursor = kwargs.get("precursor")
        framework = kwargs.get("framework")
        name = kwargs.get("name")
        description = kwargs.get("description")
        if not precursor:
            precursor = InitialThemeFactory()
        if not framework:
            framework = DescendantFrameworkFactory(precursor=precursor.framework)
        if not name:
            name = fake.sentence()
        if not description:
            description = fake.paragraph()
        return precursor.create_descendant_theme(
            new_framework=framework, name=name, description=description
        )


class ThemeMappingFactory(DjangoModelFactory):
    class Meta:
        model = models.ThemeMapping

    answer = factory.SubFactory(AnswerFactory)
    theme = factory.SubFactory(InitialThemeFactory)
    reason = factory.LazyAttribute(lambda o: fake.sentence())
    execution_run = factory.SubFactory(ExecutionRunFactory)
