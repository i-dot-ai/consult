import random

import factory
import faker as _faker
import yaml

from consultation_analyser.consultations import models

faker = _faker.Faker()

default_multiple_choice_options = ["Yes", "No", "Not sure"]


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

    def all_questions(self):
        return list(self.questions.values())


class ConsultationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Consultation
        skip_postgeneration_save = True

    name = faker.sentence()
    slug = faker.slug()

    @factory.post_generation
    def with_question(consultation, creation_strategy, value, **kwargs):
        if value is True:
            SectionFactory(
                consultation=consultation,
                with_question=True,
                with_question__with_answer=kwargs.get("with_answer"),
                with_question__with_multiple_choice=kwargs.get("with_multiple_choice"),
                with_question__with_free_text=kwargs.get("with_free_text"),
            )


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Section
        skip_postgeneration_save = True

    name = faker.sentence()
    slug = faker.slug()
    consultation = factory.SubFactory("tests.factories.ConsultationFactory")

    class Params:
        with_questions = factory.Trait(questions=[factory.SubFactory("tests.factories.QuestionFactory")])

    @factory.post_generation
    def with_question(section, creation_strategy, value, **kwargs):
        if value is True:
            QuestionFactory(
                section=section,
                with_answer=kwargs.get("with_answer"),
            )


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Question
        skip_postgeneration_save = True

    text = faker.sentence()
    slug = faker.slug()
    multiple_choice_options = ["Yes", "No", "Maybe"]
    has_free_text = True
    section = factory.SubFactory(SectionFactory)

    @factory.post_generation
    def with_answer(question, creation_strategy, value, **kwargs):
        if value is True:
            answer = AnswerFactory(question=question)
            answer.save()


class ConsultationResponseFactory(factory.django.DjangoModelFactory):
    consultation = factory.SubFactory(ConsultationFactory)

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
        skip_postgeneration_save = True

    free_text = factory.LazyAttribute(lambda o: faker.sentence() if o.question.has_free_text else None)

    question = factory.SubFactory(QuestionFactory)
    consultation_response = factory.SubFactory(ConsultationResponseFactory)
    theme = factory.LazyAttribute(lambda o: ThemeFactory() if o.free_text else None)

    multiple_choice_responses = factory.LazyAttribute(
        lambda o: random.choice(o.question.multiple_choice_options) if o.question.multiple_choice_options else None
    )
