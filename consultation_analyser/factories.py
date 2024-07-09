import random

import factory
import faker as _faker
import yaml
from django.utils import timezone

from consultation_analyser.authentication import models as authentication_models
from consultation_analyser.consultations import models
from consultation_analyser.pipeline.backends.dummy_llm_backend import DummyLLMBackend
from consultation_analyser.pipeline.backends.dummy_topic_backend import DummyTopicBackend
from consultation_analyser.pipeline.processing import process_consultation_themes

faker = _faker.Faker()


def generate_dummy_topic_keywords():
    dummy_sentence = faker.sentence()
    words = dummy_sentence.lower().strip(".")
    return words.split(" ")


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


class ConsultationWithThemesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Consultation
        skip_postgeneration_save = True

    name = factory.LazyAttribute(lambda _o: faker.sentence())
    slug = factory.LazyAttribute(lambda _o: faker.slug())

    @factory.post_generation
    def users(consultation, create, extracted, **kwargs):
        if not create or not extracted:
            return

        consultation.users.add(extracted)

    @factory.post_generation
    def create_themes(consultation, _create, _extracted, **kwargs):
        QuestionFactory(section=SectionFactory(consultation=consultation), has_free_text=True)
        ConsultationResponseFactory.create_batch(8, consultation=consultation)

        process_consultation_themes(
            consultation=consultation,
            topic_backend=DummyTopicBackend(),
            llm_backend=DummyLLMBackend(),
        )


class ConsultationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Consultation
        skip_postgeneration_save = True

    name = factory.LazyAttribute(lambda _o: faker.sentence())
    slug = factory.LazyAttribute(lambda _o: faker.slug())

    @factory.post_generation
    def with_question(consultation, creation_strategy, value, **kwargs):
        if value is True:
            SectionFactory(
                consultation=consultation,
                with_question=True,
                with_question__with_answer=kwargs.get("with_answer"),
            )

    @factory.post_generation
    def user(consultation, creation_strategy, value, **kwargs):
        if value:
            consultation.users.set([value])


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Section
        skip_postgeneration_save = True

    name = faker.sentence()
    slug = faker.slug()
    consultation = factory.SubFactory("consultation_analyser.factories.ConsultationFactory")

    class Params:
        with_questions = factory.Trait(
            questions=[factory.SubFactory("consultation_analyser.factories.QuestionFactory")]
        )

    @factory.post_generation
    def with_question(section, creation_strategy, value, **kwargs):
        if value is True:
            QuestionFactory(
                section=section,
                with_answer=kwargs.get("with_answer"),
            )


def get_multiple_choice_questions(current_question):
    if not current_question.multiple_choice_questions:
        questions = [("Do you agree?", ["Yes", "No"])]
    else:
        questions = current_question.multiple_choice_questions

    multiple_choice = []
    for question, options in questions:
        multiple_choice.append({"question_text": question, "options": options})

    return multiple_choice


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Question
        skip_postgeneration_save = True

    text = faker.sentence()
    slug = faker.slug()
    multiple_choice_options = factory.LazyAttribute(get_multiple_choice_questions)
    has_free_text = True
    section = factory.SubFactory(SectionFactory)

    class Params:
        multiple_choice_questions = None

    @factory.post_generation
    def with_answer(question, creation_strategy, value, **kwargs):
        if value is True:
            answer = AnswerFactory(
                question=question, consultation_response__consultation=question.section.consultation
            )
            answer.save()

    @factory.post_generation
    def validate_json_fields(question, creation_strategy, extracted, **kwargs):
        question.full_clean()


class ConsultationResponseFactory(factory.django.DjangoModelFactory):
    consultation = factory.SubFactory(ConsultationFactory)
    submitted_at = timezone.now()

    class Meta:
        model = models.ConsultationResponse

    @factory.post_generation
    def answers(consultation_response, creation_strategy, value, **kwargs):
        questions = models.Question.objects.filter(
            section__consultation=consultation_response.consultation
        ).all()
        for q in questions:
            AnswerFactory(question=q, consultation_response=consultation_response)


class ProcessingRunFactory(factory.django.DjangoModelFactory):
    consultation = factory.SubFactory(ConsultationFactory)

    class Meta:
        model = models.ProcessingRun


class TopicModelMetadataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TopicModelMetadata


class ThemeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Theme

    processing_run = factory.SubFactory(ProcessingRunFactory)
    topic_model_metadata = factory.SubFactory(TopicModelMetadataFactory)
    topic_keywords = factory.LazyAttribute(lambda _o: generate_dummy_topic_keywords())
    short_description = factory.LazyAttribute(lambda _o: faker.sentence())
    summary = factory.LazyAttribute(lambda _o: faker.sentence())
    topic_id = factory.Sequence(lambda n: n - 1)  # Hack to get topics to include outliers -1


def get_multiple_choice_answers(current_answer):
    multiple_choice = []
    if (
        current_answer.question.multiple_choice_options
        and not current_answer.multiple_choice_answers
    ):
        answers = [
            (q["question_text"], [random.choice(q["options"])])
            for q in current_answer.question.multiple_choice_options
        ]
    elif current_answer.question.multiple_choice_options:
        answers = current_answer.multiple_choice_answers
    else:
        return None

    for question, options in answers:
        multiple_choice.append({"question_text": question, "options": options})

    return multiple_choice


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Answer
        skip_postgeneration_save = True

    free_text = factory.LazyAttribute(
        lambda o: faker.sentence() if o.question.has_free_text else None
    )

    multiple_choice = factory.LazyAttribute(get_multiple_choice_answers)

    class Params:
        multiple_choice_answers = None

    @factory.post_generation
    def with_themes(self, creation_strategy, value, **kwargs):
        if value is True:
            processing_run = ProcessingRunFactory(consultation=self.question.section.consultation)
            theme = ThemeFactory(processing_run=processing_run)
            self.themes.add(theme)

    @factory.post_generation
    def validate_json_fields(answer, creation_strategy, extracted, **kwargs):
        answer.full_clean()


# this delegates all creation to the create_user method on User
# because that's how Django likes users to be created
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = authentication_models.User
        skip_postgeneration_save = True

    email = factory.LazyAttribute(lambda o: faker.email())
    is_staff = False
    password = factory.LazyAttribute(lambda o: faker.password())

    @factory.post_generation
    def create_user(user, creation_strategy, value, **kwargs):
        user.set_password(user.password)
        user.save()
