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


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Section

    name = faker.sentence()
    slug = faker.slug()
    consultation = factory.SubFactory(ConsultationFactory)


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Question

    text = factory.LazyAttribute(lambda o: o.question["text"])
    slug = factory.LazyAttribute(lambda o: o.question["slug"])
    multiple_choice_options = factory.LazyAttribute(lambda o: o.question["multiple_choice_options"])
    has_free_text = factory.LazyAttribute(lambda o: o.question["has_free_text"])
    section = factory.SubFactory(SectionFactory)

    class Params:
        question = FakeConsultationData().question()


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
    theme = factory.SubFactory(ThemeFactory)
