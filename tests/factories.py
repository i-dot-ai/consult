import factory
import yaml
import random
from consultation_analyser.consultations import models

import faker as _faker

faker = _faker.Faker()


class FakeConsultationData:
    def __init__(self):
        with open("./tests/examples/questions.yml", "r") as f:
            questions = yaml.safe_load(f)
            slugs = [q["slug"] for q in questions]
            self.questions = dict(zip(slugs, questions))

    def question(self):
        return random.choice(list(self.questions.values()))

    def get_free_text_answer(self, slug):
        q = self.questions[slug]
        return random.choice(q["answers"])

    def get_multiple_choice_answer(self, slug):
        q = self.questions[slug]
        return random.choice(q["multiple_choice_options"])

    def all_questions(self):
        return list(self.questions.values())


class ConsultationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Consultation

    name = faker.sentence()
    slug = faker.slug()

    class Params:
        fixed_slug = factory.Trait(slug="consultation-slug")


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Section

    name = faker.sentence()
    slug = faker.slug()

    class Params:
        fixed_slug = factory.Trait(
            slug="section-slug", consultation=factory.SubFactory(ConsultationFactory, fixed_slug=True)
        )


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Question

    text = factory.LazyAttribute(lambda o: o.question["text"])
    slug = factory.LazyAttribute(lambda o: o.question["slug"])
    multiple_choice_options = factory.LazyAttribute(lambda o: o.question["multiple_choice_options"])
    has_free_text = factory.LazyAttribute(lambda o: o.question["has_free_text"])

    class Params:
        question = FakeConsultationData().question()

        fixed_slug = factory.Trait(
            section=factory.SubFactory(SectionFactory, fixed_slug=True),
            slug="question-slug",
            text="Is this an interesting question?",
            multiple_choice_options=[],
            has_free_text=False,
        )


class ConsultationResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ConsultationResponse


class ThemeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Theme

    # TODO - may need to be changed once ML pipeline is in
    label = faker.sentence()
    summary = f"Summary: {label}"
    keywords = label.lower().strip(".").split(" ")


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Answer

    multiple_choice_responses = factory.LazyAttribute(
        lambda o: FakeConsultationData().get_multiple_choice_answer(o.question.slug)
        if o.question.multiple_choice_options
        else None
    )

    free_text = factory.LazyAttribute(
        lambda o: FakeConsultationData().get_free_text_answer(o.question.slug) if o.question.has_free_text else None
    )

    question = factory.SubFactory(QuestionFactory)
    consultation_response = factory.SubFactory(ConsultationResponseFactory)

    class Params:
        specific_theme = factory.Trait(
            consultation_response=factory.SubFactory(ConsultationResponseFactory),
            question=factory.SubFactory(QuestionFactory, fixed_slug=True),
            theme=factory.SubFactory(ThemeFactory, summary="Summary theme 1", keywords=["summary", "one"]),
        )
