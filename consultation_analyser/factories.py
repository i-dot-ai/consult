import random

import factory
from django.utils import timezone
from factory import fuzzy
from factory.django import DjangoModelFactory
from faker import Faker

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models
from consultation_analyser.consultations.models import DemographicOption, MultiChoiceAnswer
from consultation_analyser.embeddings import embed_text

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

    consultation = factory.SubFactory(ConsultationFactory)
    text = factory.LazyAttribute(lambda o: fake.sentence())
    number = factory.Sequence(lambda n: n + 1)
    has_free_text = True
    has_multiple_choice = False


class MultiChoiceAnswerFactory(DjangoModelFactory):
    text = factory.Faker("word")
    question = factory.SubFactory(QuestionFactory)

    class Meta:
        model = MultiChoiceAnswer


class QuestionWithMultipleChoiceFactory(QuestionFactory):
    has_free_text = False
    has_multiple_choice = True

    @factory.post_generation
    def create_multiple_choice_responses(self, create, extracted, **kwargs):
        if not create:
            return
        MultiChoiceAnswerFactory.create_batch(random.randint(2, 5), question=self)


class QuestionWithBothFactory(QuestionFactory):
    has_free_text = True
    has_multiple_choice = True

    @factory.post_generation
    def create_multiple_choice_responses(self, create, extracted, **kwargs):
        if not create:
            return

        MultiChoiceAnswerFactory.create_batch(random.randint(2, 5), question=self)


class RespondentFactory(DjangoModelFactory):
    class Meta:
        model = models.Respondent

    consultation = factory.SubFactory(ConsultationFactory)
    themefinder_id = factory.LazyAttribute(lambda o: random.randint(2, 500000000))

    @factory.post_generation
    def demographics(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        if not extracted:
            extracted = {
                "Nation": random.choice(["England", "Wales", "Northern Ireland", "Scotland"]),
                "Age": random.choice(["Under 18", "18-35", "36-50", "51-65", "66+"]),
            }

        def encode(obj):
            if isinstance(obj, bool):
                return obj
            return str(obj)

        for k, v in extracted.items():
            o, _ = DemographicOption.objects.get_or_create(
                consultation=self.consultation,
                field_name=k,
                field_value=encode(v),
            )
            self.demographics.add(o)
        self.save()


class ResponseFactory(DjangoModelFactory):
    class Meta:
        model = models.Response

    respondent = factory.SubFactory(RespondentFactory)
    question = factory.SubFactory(QuestionFactory)
    free_text = factory.LazyAttribute(lambda o: fake.paragraph())
    embedding = factory.LazyAttribute(lambda o: embed_text(o.free_text))


class ResponseWithMultipleChoiceFactory(ResponseFactory):
    question = factory.SubFactory(QuestionWithMultipleChoiceFactory)
    free_text = ""

    @factory.post_generation
    def themes(self, create, extracted, **kwargs):
        if not create:
            return

        chosen_options = random.sample(
            self.question.multiple_choice_options,
            k=random.randint(1, len(self.question.multiple_choice_options)),
        )
        self.chosen_options.set(chosen_options)
        self.save()


class ResponseWithBothFactory(ResponseFactory):
    question = factory.SubFactory(QuestionWithBothFactory)
    free_text = factory.LazyAttribute(lambda o: fake.paragraph())

    @factory.post_generation
    def themes(self, create, extracted, **kwargs):
        if not create:
            return
        chosen_options = random.sample(
            self.question.multiple_choice_options,
            k=random.randint(1, len(self.question.multiple_choice_options)),
        )
        self.chosen_options.set(chosen_options)
        self.save()


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
    evidence_rich = fuzzy.FuzzyChoice([True, False])
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

    @factory.post_generation
    def flagged_by(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.flagged_by.set(extracted)
        self.save()


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
