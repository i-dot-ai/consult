import pytest
from django.conf import settings

from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_upload_consultation():
    file = open(settings.BASE_DIR / "tests" / "examples" / "upload.json", "r")
    user = UserFactory()

    consultation = upload_consultation(file, user)

    assert consultation.section_set.count() == 1

    section = consultation.section_set.first()
    assert section.question_set.count() == 2

    assert consultation.consultationresponse_set.count() == 2

    responses = consultation.consultationresponse_set.prefetch_related("answer_set", "answer_set__question").all()

    for response in responses:
        answers = response.answer_set.all()
        assert answers.count() == 2

        for a in answers:
            q = a.question
            assert q.text in ["Question 1", "Question 2"]
            if q.text == "Question 1":
                assert a.free_text == "Answer to Question 1"
            elif q.text == "Question 2":
                assert a.free_text == "Answer to Question 2"
