import pytest
from django.urls import reverse

from consultations.models import Response
from factories import RespondentFactory


@pytest.fixture
def question_detail_url():
    def _url(question):
        return reverse(
            "question-v2-detail",
            kwargs={"consultation_pk": question.consultation_id, "pk": question.id},
        )

    return _url


@pytest.fixture
def demographics_url():
    def _url(consultation, question):
        return reverse(
            "question-v2-demographics",
            kwargs={"consultation_pk": consultation.id, "pk": question.id},
        )

    return _url


@pytest.fixture
def merge_url():
    def _url(consultation, question):
        return reverse(
            "question-v2-merge-demographics",
            kwargs={"consultation_pk": consultation.id, "pk": question.id},
        )

    return _url


@pytest.fixture
def demographic_response():
    def _create(question, text):
        return Response.objects.create(
            question=question,
            respondent=RespondentFactory(consultation=question.consultation),
            text=text,
        )

    return _create
