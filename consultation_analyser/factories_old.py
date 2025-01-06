import random

import factory
import faker as _faker
from django.utils import timezone

from consultation_analyser.authentication import models as authentication_models
from consultation_analyser.consultations import models

faker = _faker.Faker()


def generate_dummy_topic_keywords():
    dummy_sentence = faker.sentence()
    words = dummy_sentence.lower().strip(".")
    return words.split(" ")


class ConsultationBuilder:
    def __init__(self, **kwargs):
        consultation = ConsultationFactory(**kwargs)

        self.consultation = consultation
        self.current_response = None
        self.current_processing_run = None
        self.section = None
        self.consultation_responses = []

    def get_section(self):
        if not self.section:
            self.section = SectionFactory(consultation=self.consultation)

        return self.section

    def add_question(self, **kwargs):
        """
        Create a question, assigning it to the current section.
        We only support one section for now.
        """
        return QuestionFactory(section=self.get_section(), **kwargs)

    def add_answer(self, question, **kwargs):
        """
        Create an answer to the passed question, assigning it to the current_response
        """
        return AnswerFactory(
            question=question, consultation_response=self.get_current_response(), **kwargs
        )

    def next_response(self):
        """
        Create a new response and put it in the self.current_response
        field
        """
        self.current_response = None
        return self.get_current_response()

    def get_current_response(self):
        """
        Return the current_response, creating one if it doesn't exist
        """
        if not self.current_response:
            self.current_response = ConsultationResponseFactory(
                consultation=self.consultation, answers=False
            )

        return self.current_response

    def get_current_processing_run(self):
        if not self.current_processing_run:
            self.current_processing_run = ProcessingRunFactory(consultation=self.consultation)

        return self.current_processing_run

    def add_theme(self, answer=None, **kwargs):
        """
        Create a theme, optionally passing an Answer to assign it to
        """

        processing_run = self.get_current_processing_run()
        theme = ThemeFactory(processing_run=processing_run, **kwargs)

        if answer:
            answer.themes.add(theme)

        return theme


class ConsultationWithAnswersFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ConsultationOld
        skip_postgeneration_save = True

    name = factory.LazyAttribute(lambda _o: faker.sentence())
    slug = factory.LazyAttribute(lambda _o: faker.slug())

    @factory.post_generation
    def users(consultation, create, extracted, **kwargs):
        if not create or not extracted:
            return

        consultation.users.add(extracted)

    @factory.post_generation
    def create_answers(consultation, _create, _extracted, **kwargs):
        QuestionFactory(section=SectionFactory(consultation=consultation))
        ConsultationResponseFactory.create_batch(8, consultation=consultation)


class ConsultationWithThemesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ConsultationOld
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
        QuestionFactory(section=SectionFactory(consultation=consultation))
        ConsultationResponseFactory.create_batch(8, consultation=consultation)


class ConsultationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ConsultationOld
        skip_postgeneration_save = True

    name = factory.LazyAttribute(lambda _o: faker.sentence())
    slug = factory.LazyAttribute(lambda _o: faker.slug())

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
        model = models.QuestionOld
        skip_postgeneration_save = True

    text = factory.LazyAttribute(lambda _o: faker.sentence())
    slug = factory.LazyAttribute(lambda _o: faker.slug())
    multiple_choice_options = factory.LazyAttribute(get_multiple_choice_questions)
    has_free_text = True
    section = factory.SubFactory(SectionFactory)

    class Params:
        multiple_choice_questions = None

    @factory.post_generation
    def validate_json_fields(question, creation_strategy, extracted, **kwargs):
        question.full_clean()


class ConsultationResponseFactory(factory.django.DjangoModelFactory):
    consultation = factory.SubFactory(ConsultationFactory)
    submitted_at = timezone.now()

    class Meta:
        model = models.ConsultationResponse
        skip_postgeneration_save = True

    @factory.post_generation
    def answers(consultation_response, creation_strategy, value, **kwargs):
        if value or value is None:
            questions = models.QuestionOld.objects.filter(
                section__consultation=consultation_response.consultation
            ).all()
            for q in questions:
                AnswerFactory(question=q, consultation_response=consultation_response)


class ProcessingRunFactory(factory.django.DjangoModelFactory):
    consultation = factory.SubFactory(ConsultationFactory)
    started_at = timezone.now() - timezone.timedelta(minutes=1)
    finished_at = timezone.now()

    class Meta:
        model = models.ProcessingRun


class TopicModelMetadataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TopicModelMetadata


class ThemeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ThemeOld

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
        model = models.AnswerOld
        skip_postgeneration_save = True

    free_text = factory.LazyAttribute(
        lambda o: faker.sentence() if o.question.has_free_text else None
    )

    multiple_choice = factory.LazyAttribute(get_multiple_choice_answers)

    class Params:
        multiple_choice_answers = None

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
