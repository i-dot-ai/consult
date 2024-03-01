import factory
from consultation_analyser.consultations import models


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Question

    text = "Example question text?"
    slug = "test-question"
