import random

import factory
from factory import fuzzy
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

    title = factory.LazyAttribute(lambda o: fake.sentence())


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = models.Question

    text = factory.LazyAttribute(lambda o: fake.sentence())
    consultation = factory.SubFactory(ConsultationFactory)
    number = factory.Sequence(lambda n: n + 1)  # Unique number within consultation


class FreeTextQuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(QuestionFactory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.FREE_TEXT
    number = factory.Sequence(lambda n: n + 1)  # Unique number within question


class SingleOptionQuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(QuestionFactory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.SINGLE_OPTION
    number = factory.Sequence(lambda n: n + 1)  # Unique number within question
    options = factory.LazyAttribute(lambda o: [fake.word() for _ in range(random.randint(2, 5))])


class MultipleOptionQuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(QuestionFactory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.MULTIPLE_OPTIONS
    number = factory.Sequence(lambda n: n + 1)  # Unique number within question
    options = factory.LazyAttribute(lambda o: [fake.word() for _ in range(random.randint(2, 5))])


class RespondentFactory(DjangoModelFactory):
    class Meta:
        model = models.Respondent

    consultation = factory.SubFactory(ConsultationFactory)
    themefinder_respondent_id = factory.LazyAttribute(lambda o: random.randint(2, 500000000))


class FreeTextAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.Answer

    question_part = factory.SubFactory(FreeTextQuestionPartFactory)
    respondent = factory.SubFactory(RespondentFactory)
    text = factory.LazyAttribute(lambda o: fake.paragraph())


class SingleOptionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.Answer

    question_part = factory.SubFactory(SingleOptionQuestionPartFactory)
    respondent = factory.SubFactory(RespondentFactory)
    chosen_options = factory.LazyAttribute(lambda o: [random.choice(o.question_part.options)])


class MultipleOptionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.Answer

    question_part = factory.SubFactory(MultipleOptionQuestionPartFactory)
    respondent = factory.SubFactory(RespondentFactory)
    chosen_options = factory.LazyAttribute(
        lambda o: random.sample(
            o.question_part.options, k=random.randint(1, len(o.question_part.options))
        )
    )


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
        theme_generation_execution_run = kwargs.get("theme_generation_execution_run")
        question_part = kwargs.get("question_part")
        if not theme_generation_execution_run:
            theme_generation_execution_run = ExecutionRunFactory(
                type=models.ExecutionRun.TaskType.THEME_GENERATION
            )
        if not question_part:
            question_part = FreeTextQuestionPartFactory()
        return model_class.create_initial_framework(
            theme_generation_execution_run=theme_generation_execution_run,
            question_part=question_part,
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
        key = kwargs.get("key")
        if not framework:
            framework = InitialFrameworkFactory()
        if not name:
            name = fake.sentence()
        if not description:
            description = fake.paragraph()
        if not key:
            key = fake.random_letter()
        return model_class.create_initial_theme(
            framework=framework, name=name, description=description, key=key
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
        key = kwargs.get("key")
        if not precursor:
            precursor = InitialThemeFactory()
        if not framework:
            framework = DescendantFrameworkFactory(precursor=precursor.framework)
        if not name:
            name = fake.sentence()
        if not description:
            description = fake.paragraph()
        if not key:
            key = fake.random_letter()
        return precursor.create_descendant_theme(
            new_framework=framework, name=name, description=description, key=key
        )


class ThemeMappingFactory(DjangoModelFactory):
    class Meta:
        model = models.ThemeMapping

    answer = factory.SubFactory(FreeTextAnswerFactory)
    theme = factory.SubFactory(InitialThemeFactory)
    reason = factory.LazyAttribute(lambda o: fake.sentence())
    theme_mapping_execution_run = factory.SubFactory(ExecutionRunFactory)
    stance = fuzzy.FuzzyChoice(models.ThemeMapping.Stance.values)


class SentimentMappingFactory(DjangoModelFactory):
    class Meta:
        model = models.SentimentMapping

    answer = factory.SubFactory(FreeTextAnswerFactory)
    sentiment_analysis_execution_run = factory.SubFactory(ExecutionRunFactory)
    position = fuzzy.FuzzyChoice(models.SentimentMapping.Position.values)
