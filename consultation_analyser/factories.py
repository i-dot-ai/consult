import random

import factory
from django.utils import timezone
from factory import fuzzy
from factory.django import DjangoModelFactory
from faker import Faker

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models
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
    demographics = factory.LazyAttribute(
        lambda o: {
            "Nation": random.choice(["England", "Wales", "Northern Ireland", "Scotland"]),
            "Age": random.choice(["Under 18", "18-35", "36-50", "51-65", "66+"]),
        }
    )


class ResponseFactory(DjangoModelFactory):
    class Meta:
        model = models.Response

    respondent = factory.SubFactory(RespondentFactory)
    question = factory.SubFactory(QuestionFactory)
    free_text = factory.LazyAttribute(lambda o: fake.paragraph())
    chosen_options = factory.LazyFunction(list)  # Empty list
    embedding = factory.LazyAttribute(lambda o: embed_text(o.free_text))


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
