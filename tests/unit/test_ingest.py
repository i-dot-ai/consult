import pytest
import time

from consultation_analyser import factories
from consultation_analyser.consultations.models import (
    Answer,
    QuestionPart,
    Respondent,
)
from consultation_analyser.support_console.ingest import (
    import_question_part_data,
    import_responses,
    import_all_responses_from_jsonl
)

# TODO - keep for a while to see how to test reading from bucket
# def test_get_themefinder_outputs_for_question(mock_s3_objects, monkeypatch):
#     monkeypatch.setattr(settings, "AWS_BUCKET_NAME", "test-bucket")
#     outputs = get_themefinder_outputs_for_question("folder/question_0/", "question")
#     assert outputs.get("question") == "What do you think?"
#     outputs = get_themefinder_outputs_for_question("folder/question_0/", "updated_mapping")
#     assert outputs[1].get("response_id") == 1
#     assert outputs[1].get("labels") == ["C", "D"]
#     outputs = get_themefinder_outputs_for_question("folder/question_0/", "themes")
#     assert len(outputs) == 5
#     outputs = get_themefinder_outputs_for_question("folder/question_1/", "themes")
#     assert len(outputs) == 3


@pytest.mark.django_db
def test_import_question_part_data():
    consultation = factories.ConsultationFactory()
    # Set up sample question_part.json dictionaries
    new_free_text_question = {
        "question_text": "What is your favourite?",
        "question_part_text": "Please explain your answer",
        "question_number": 3,
        "question_part_type": "free_text",
    }
    existing_question_with_options = {
        "question_text": "What is your favourite?",
        "question_number": 3,
        "question_part_number": 2,
        "options": ["cats", "dogs"],
        "question_part_type": "single_option",
    }
    failing_no_text = {
        "question_text": "",
        "question_part_text": "",
        "question_number": 4,
        "question_part_type": "free_text",
    }
    failing_no_question_number = {
        "question_text": "What is your favourite?",
        "question_part_type": "free_text",
    }

    import_question_part_data(consultation=consultation, question_part_dict=new_free_text_question)
    question_part = QuestionPart.objects.get(
        question__consultation=consultation, question__number=3, number=1
    )
    assert question_part.text == "Please explain your answer"
    assert question_part.question.text == "What is your favourite?"
    assert question_part.number == 1
    assert question_part.type == QuestionPart.QuestionType.FREE_TEXT

    import_question_part_data(
        consultation=consultation, question_part_dict=existing_question_with_options
    )
    question_part = QuestionPart.objects.get(
        question__consultation=consultation, question__number=3, number=2
    )
    assert question_part.text == ""
    assert question_part.question.text == "What is your favourite?"
    assert question_part.options == ["cats", "dogs"]
    assert question_part.type == QuestionPart.QuestionType.SINGLE_OPTION

    with pytest.raises(ValueError):
        import_question_part_data(consultation=consultation, question_part_dict=failing_no_text)

    with pytest.raises(KeyError):
        import_question_part_data(
            consultation=consultation, question_part_dict=failing_no_question_number
        )


# TODO - add a test for non-free text cases
@pytest.mark.django_db
def test_import_responses():
    question_part = factories.FreeTextQuestionPartFactory()
    consultation = question_part.question.consultation
    Respondent.objects.create(consultation=consultation, themefinder_respondent_id=1)

    # Not every respondent will respond to every q
    # Some respondents will already exist, some will be created
    responses_data = [
        {"themefinder_id": 1, "response": "response 1"},
        {"themefinder_id": 2, "response": "response 2"},
        {"themefinder_id": 4, "response": "response 4"},
    ]
    import_responses(question_part=question_part, responses_data=responses_data)
    assert Respondent.objects.all().count() == 3
    assert Answer.objects.all().count() == 3

    response = Answer.objects.get(
        question_part=question_part, respondent__themefinder_respondent_id=1
    )
    assert response.text == "response 1"

    response = Answer.objects.get(
        question_part=question_part, respondent__themefinder_respondent_id=2
    )
    assert response.text == "response 2"


# TODO - make this test work

@pytest.mark.django_db
def test_import_all_responses_from_jsonl(mock_s3_bucket, mock_consultation_input_objects, monkeypatch):
    question = factories.QuestionFactory(number=3)
    question_part = factories.FreeTextQuestionPartFactory(question=question, number=1)
    import_all_responses_from_jsonl(question_part, bucket_name="test-bucket", question_part_folder_key="app_data/CON1/question_part_2/", batch_size=2)

    # TODO - is there a better way?
    time.sleep(5)

    responses = Answer.objects.filter(question_part=question_part)
    respondents = Respondent.objects.filter(consultation = question.consultation)
    assert responses.count() == 3
    assert respondents.count() == 3
    assert responses[0].respondent.themefinder_respondent_id == 1
    assert responses[0].text == "It's really fun."
    assert responses[2].text == "I need more info."
    assert responses[2].respondent.themefinder_respondent_id == 4
