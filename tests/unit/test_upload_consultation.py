import pytest
from django.conf import settings

from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_upload_consultation():
    file = open(settings.BASE_DIR / "tests" / "examples" / "upload.json", "rb")
    user = UserFactory()

    consultation = upload_consultation(file, user)

    assert consultation.section_set.count() == 1

    section = consultation.section_set.first()
    assert section.question_set.count() == 3

    assert consultation.consultationresponse_set.count() == 2

    responses = consultation.consultationresponse_set.prefetch_related(
        "answer_set", "answer_set__question"
    ).all()

    for response in responses:
        answers = response.answer_set.all()
        assert answers.count() == 3

        for a in answers:
            q = a.question
            assert q.text in ["Question 1", "Question 2", "Question 3"]
            if q.text == "Question 1":
                assert a.free_text == "Answer to Question 1"
            elif q.text == "Question 2":
                assert a.free_text == "Answer to Question 2"
                assert a.multiple_choice == [
                    {"question_text": "Do you like A, B or C?", "options": ["a"]}
                ]
            elif q.text == "Question 3":
                assert not a.free_text  # there is no free text part
                assert len(a.multiple_choice) == 2
