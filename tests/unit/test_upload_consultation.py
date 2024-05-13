import pytest
from django.conf import settings

from consultation_analyser.consultations.models import Answer, Question
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

    response = consultation.consultationresponse_set.all()[0]
    r1_answers = Answer.objects.filter(consultation_response=response).all()
    assert r1_answers.count() == 2

    response = consultation.consultationresponse_set.all()[1]
    r2_answers = Answer.objects.filter(consultation_response=response).all()
    assert r2_answers.count() == 2

    for a in Answer.objects.all():
        q = a.question
        assert a.free_text in ["Answer to Question 1", "Answer to Question 2"]
        if q.text == "Question 1":
            assert a.free_text == "Answer to Question 1"
        elif q.text == "Question 2":
            assert a.free_text == "Answer to Question 2"

