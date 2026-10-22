import pytest
from django.urls import reverse


@pytest.fixture
def question_detail_url():
    def _url(question):
        return reverse(
            "question-v2-detail",
            kwargs={"consultation_pk": question.consultation_id, "pk": question.id},
        )

    return _url
