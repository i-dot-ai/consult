import random

import factory
from django.utils import timezone
from factory import fuzzy
from factory.django import DjangoModelFactory
from faker import Faker

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models

fake = Faker()


# OLD FACTORIES


class UserFactoryOld(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda o: fake.email())
    is_staff = False
    password = factory.LazyAttribute(lambda o: fake.password())


class ConsultationFactoryOld(DjangoModelFactory):
    class Meta:
        model = models.ConsultationOld

    title = factory.LazyAttribute(lambda o: fake.sentence())


class QuestionFactoryOld(DjangoModelFactory):
    class Meta:
        model = models.QuestionOld

    text = factory.LazyAttribute(lambda o: fake.sentence())
    consultation = factory.SubFactory(ConsultationFactoryOld)
    number = factory.Sequence(lambda n: n + 1)  # Unique number within consultation


class FreeTextQuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(QuestionFactoryOld)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.FREE_TEXT
    number = factory.Sequence(lambda n: n + 1)  # Unique number within question


class SingleOptionQuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(QuestionFactoryOld)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.SINGLE_OPTION
    number = factory.Sequence(lambda n: n + 1)  # Unique number within question
    options = factory.LazyAttribute(lambda o: [fake.word() for _ in range(random.randint(2, 5))])


class MultipleOptionQuestionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.QuestionPart

    question = factory.SubFactory(QuestionFactoryOld)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    type = models.QuestionPart.QuestionType.MULTIPLE_OPTIONS
    number = factory.Sequence(lambda n: n + 1)  # Unique number within question
    options = factory.LazyAttribute(lambda o: [fake.word() for _ in range(random.randint(2, 5))])


class RespondentFactoryOld(DjangoModelFactory):
    class Meta:
        model = models.RespondentOld

    consultation = factory.SubFactory(ConsultationFactoryOld)
    themefinder_respondent_id = factory.LazyAttribute(lambda o: random.randint(2, 500000000))


class FreeTextAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.Answer

    question_part = factory.SubFactory(FreeTextQuestionPartFactory)
    respondent = factory.SubFactory(RespondentFactoryOld)
    text = factory.LazyAttribute(lambda o: fake.paragraph())


class SingleOptionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.Answer

    question_part = factory.SubFactory(SingleOptionQuestionPartFactory)
    respondent = factory.SubFactory(RespondentFactoryOld)
    chosen_options = factory.LazyAttribute(lambda o: [random.choice(o.question_part.options)])


class MultipleOptionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = models.Answer

    question_part = factory.SubFactory(MultipleOptionQuestionPartFactory)
    respondent = factory.SubFactory(RespondentFactoryOld)
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
        execution_run = kwargs.get("execution_run")
        question_part = kwargs.get("question_part")
        if not execution_run:
            execution_run = ExecutionRunFactory(type=models.ExecutionRun.TaskType.THEME_GENERATION)
        if not question_part:
            question_part = FreeTextQuestionPartFactory()
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
            user = UserFactoryOld()
        if not change_reason:
            change_reason = fake.sentence()
        return precursor.create_descendant_framework(user=user, change_reason=change_reason)


class InitialThemeFactory(DjangoModelFactory):
    # Create an initial theme (which will have come from the theme generation task)
    class Meta:
        model = models.ThemeOld

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
        model = models.ThemeOld

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
    execution_run = factory.SubFactory(ExecutionRunFactory)
    stance = fuzzy.FuzzyChoice(models.ThemeMapping.Stance.values)


class SentimentMappingFactory(DjangoModelFactory):
    class Meta:
        model = models.SentimentMapping

    answer = factory.SubFactory(FreeTextAnswerFactory)
    execution_run = factory.SubFactory(ExecutionRunFactory)
    position = fuzzy.FuzzyChoice(models.SentimentMapping.Position.values)


class EvidenceRichMappingFactory(DjangoModelFactory):
    class Meta:
        model = models.EvidenceRichMapping

    answer = factory.SubFactory(FreeTextAnswerFactory)
    evidence_evaluation_execution_run = factory.SubFactory(ExecutionRunFactory)
    evidence_rich = fake.boolean()


# NEW FACTORIES


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

    consultation = factory.SubFactory(ConsultationFactory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    number = factory.Sequence(lambda n: n + 1)
    has_free_text = True
    has_multiple_choice = False
    multiple_choice_options = None


class QuestionWithMultipleChoiceFactory(QuestionFactory):
    has_free_text = False
    has_multiple_choice = True
    multiple_choice_options = factory.LazyAttribute(
        lambda o: [fake.word() for _ in range(random.randint(2, 5))]
    )


class QuestionWithBothFactory(QuestionFactory):
    has_free_text = True
    has_multiple_choice = True
    multiple_choice_options = factory.LazyAttribute(
        lambda o: [fake.word() for _ in range(random.randint(2, 5))]
    )


class RespondentFactory(DjangoModelFactory):
    class Meta:
        model = models.Respondent

    consultation = factory.SubFactory(ConsultationFactory)
    themefinder_id = factory.LazyAttribute(lambda o: random.randint(2, 500000000))
    demographics = factory.LazyAttribute(lambda o: {"age": random.randint(18, 80)})


class ResponseFactory(DjangoModelFactory):
    class Meta:
        model = models.Response

    respondent = factory.SubFactory(RespondentFactory)
    question = factory.SubFactory(QuestionFactory)
    free_text = factory.LazyAttribute(lambda o: fake.paragraph())
    chosen_options = factory.LazyFunction(list)  # Empty list


class ResponseWithMultipleChoiceFactory(ResponseFactory):
    question = factory.SubFactory(QuestionWithMultipleChoiceFactory)
    free_text = ""
    chosen_options = factory.LazyAttribute(
        lambda o: random.sample(
            o.question.multiple_choice_options,
            k=random.randint(1, len(o.question.multiple_choice_options)),
        )
    )


class ResponseWithBothFactory(ResponseFactory):
    question = factory.SubFactory(QuestionWithBothFactory)
    free_text = factory.LazyAttribute(lambda o: fake.paragraph())
    chosen_options = factory.LazyAttribute(
        lambda o: random.sample(
            o.question.multiple_choice_options,
            k=random.randint(1, len(o.question.multiple_choice_options)),
        )
    )


class ThemeFactory(DjangoModelFactory):
    class Meta:
        model = models.Theme

    question = factory.SubFactory(QuestionFactory)
    name = factory.LazyAttribute(lambda o: fake.sentence())
    description = factory.LazyAttribute(lambda o: fake.paragraph())
    key = factory.Sequence(lambda n: f"theme-{n}")


class ResponseAnnotationFactory(DjangoModelFactory):
    class Meta:
        model = models.ResponseAnnotation

    response = factory.SubFactory(ResponseFactory)
    sentiment = fuzzy.FuzzyChoice(models.ResponseAnnotation.Sentiment.values)
    evidence_rich = fuzzy.FuzzyChoice(models.ResponseAnnotation.EvidenceRich.values)
    human_reviewed = False
    reviewed_by = None
    reviewed_at = None

    @factory.post_generation
    def themes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # If themes were passed in, use the proper helper method
            self.add_original_ai_themes(extracted)
        else:
            # Create some themes for the same question
            num_themes = random.randint(1, 3)
            themes_to_add = []
            for _ in range(num_themes):
                theme = ThemeFactory(question=self.response.question)
                themes_to_add.append(theme)
            self.add_original_ai_themes(themes_to_add)


class ReviewedResponseAnnotationFactory(ResponseAnnotationFactory):
    human_reviewed = True
    reviewed_by = factory.SubFactory(UserFactory)
    reviewed_at = factory.LazyAttribute(lambda o: timezone.now())


class ResponseAnnotationFactoryNoThemes(ResponseAnnotationFactory):
    """Factory that doesn't automatically create themes"""
    class Meta:
        model = models.ResponseAnnotation
        skip_postgeneration_save = True
    
    @factory.post_generation
    def themes(self, create, extracted, **kwargs):
        # Don't create any themes automatically
        pass
