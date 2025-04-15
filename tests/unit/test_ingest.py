import time

import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import (
    Answer,
    QuestionPart,
    Respondent,
    SentimentMapping,
    Theme,
    ThemeMapping,
)
from consultation_analyser.support_console.ingest import (
    import_all_respondents_from_jsonl,
    import_all_responses_from_jsonl,
    import_all_sentiment_mappings_from_jsonl,
    import_all_theme_mappings_from_jsonl,
    import_question_part_data,
    import_respondent_data,
    import_responses,
    import_sentiment_mappings,
    import_theme_mappings,
    import_themes,
    import_themes_from_json,
)


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
    for i in range(1, 5):
        factories.RespondentFactory(consultation=consultation, themefinder_respondent_id=i)
    responses_data = [
        b'{"themefinder_id":1, "text":"response 1"}',
        b'{"themefinder_id":2, "text":"response 2"}',
        b'{"themefinder_id":4, "text":"response 4"}',
    ]

    import_responses(question_part=question_part, responses_data=responses_data)
    assert Answer.objects.all().count() == 3
    response = Answer.objects.get(
        question_part=question_part, respondent__themefinder_respondent_id=1
    )
    assert response.text == "response 1"
    response = Answer.objects.get(
        question_part=question_part, respondent__themefinder_respondent_id=2
    )
    assert response.text == "response 2"


@pytest.mark.django_db
def test_import_all_responses_from_jsonl(mock_consultation_input_objects):
    question = factories.QuestionFactory(number=3)
    question_part = factories.FreeTextQuestionPartFactory(question=question, number=1)
    consultation = question.consultation
    for i in range(1, 6):
        factories.RespondentFactory(consultation=consultation, themefinder_respondent_id=i)
    import_all_responses_from_jsonl(
        question_part,
        bucket_name="test-bucket",
        question_part_folder_key="app_data/CON1/inputs/question_part_2/",
        batch_size=2,
    )
    # TODO - improve this, but it works for now!
    time.sleep(5)
    responses = Answer.objects.filter(question_part=question_part)
    assert responses.count() == 3
    assert responses[0].respondent.themefinder_respondent_id == 1
    assert responses[0].text == "It's really fun."
    assert responses[2].text == "I need more info."
    assert responses[2].respondent.themefinder_respondent_id == 4


@pytest.mark.django_db
def test_import_respondent_data():
    respondent_data = [
        b'{"themefinder_id":1}',
        b'{"themefinder_id":2}',
        b'{"themefinder_id":3}',
    ]
    consultation = factories.ConsultationFactory()
    import_respondent_data(consultation=consultation, respondent_data=respondent_data)
    respondents = Respondent.objects.filter(consultation=consultation).order_by(
        "themefinder_respondent_id"
    )
    assert respondents.count() == 3
    assert respondents[0].themefinder_respondent_id == 1
    assert respondents[2].themefinder_respondent_id == 3


@pytest.mark.django_db
def test_import_all_respondents_from_jsonl(mock_consultation_input_objects):
    consultation = factories.ConsultationFactory()
    import_all_respondents_from_jsonl(
        consultation=consultation,
        bucket_name="test-bucket",
        inputs_folder_key="app_data/CON1/inputs/",
        batch_size=2,
    )
    # TODO - improve this, but it works for now!
    time.sleep(5)
    respondents = Respondent.objects.filter(consultation=consultation).order_by(
        "themefinder_respondent_id"
    )
    assert respondents.count() == 5
    assert respondents[0].themefinder_respondent_id == 1
    assert respondents[4].themefinder_respondent_id == 5


@pytest.mark.django_db
def test_import_themes():
    theme_data = [
        {"theme_key": "A", "theme_name": "Theme A", "theme_description": "A description"},
        {"theme_key": "B", "theme_name": "Theme B", "theme_description": "B description"},
        {"theme_key": "C", "theme_name": "Theme C", "theme_description": "C description"},
    ]
    question_part = factories.FreeTextQuestionPartFactory()
    import_themes(question_part=question_part, theme_data=theme_data)
    themes = Theme.objects.filter(framework__question_part=question_part).order_by("key")
    assert themes.count() == 3
    assert themes[0].key == "A"
    assert themes[2].key == "C"


@pytest.mark.django_db
def test_import_themes_from_json(mock_consultation_input_objects):
    question_part = factories.FreeTextQuestionPartFactory()
    import_themes_from_json(
        question_part=question_part,
        bucket_name="test-bucket",
        question_part_folder_key="app_data/CON1/outputs/mapping/2025-04-01/question_part_1/",
    )
    # TODO - improve this, but it works for now!
    time.sleep(5)
    themes = Theme.objects.filter(framework__question_part=question_part).order_by("key")
    assert themes.count() == 3
    assert themes[0].key == "A"
    assert themes[2].key == "C"


@pytest.mark.django_db
def test_import_theme_mappings():
    thememapping_data = [
        b'{"themefinder_id":1,"theme_keys":["A"]}',
        b'{"themefinder_id":2,"theme_keys":["B"]}',
        b'{"themefinder_id":3,"theme_keys":["A", "B"]}',
    ]
    question_part = factories.FreeTextQuestionPartFactory()
    consultation = question_part.question.consultation
    respondent_1 = factories.RespondentFactory(
        themefinder_respondent_id=1, consultation=consultation
    )
    respondent_2 = factories.RespondentFactory(
        themefinder_respondent_id=2, consultation=consultation
    )
    respondent_3 = factories.RespondentFactory(
        themefinder_respondent_id=3, consultation=consultation
    )
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_1)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_2)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_3)

    framework = factories.InitialFrameworkFactory(question_part=question_part)

    factories.InitialThemeFactory(key="A", framework=framework)
    factories.InitialThemeFactory(key="B", framework=framework)

    import_theme_mappings(question_part=question_part, thememapping_data=thememapping_data)
    theme_mappings = ThemeMapping.objects.filter(answer__question_part=question_part).order_by(
        "answer__respondent__themefinder_respondent_id", "theme__key"
    )
    assert theme_mappings.count() == 4
    assert theme_mappings[0].theme.key == "A"
    assert theme_mappings[3].theme.key == "B"


@pytest.mark.django_db
def test_import_all_theme_mappings_from_jsonl(mock_consultation_input_objects):
    question_part = factories.FreeTextQuestionPartFactory()
    consultation = question_part.question.consultation
    respondent_1 = factories.RespondentFactory(
        themefinder_respondent_id=1, consultation=consultation
    )
    respondent_2 = factories.RespondentFactory(
        themefinder_respondent_id=2, consultation=consultation
    )
    respondent_3 = factories.RespondentFactory(
        themefinder_respondent_id=3, consultation=consultation
    )
    respondent_4 = factories.RespondentFactory(
        themefinder_respondent_id=4, consultation=consultation
    )
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_1)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_2)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_3)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_4)

    framework = factories.InitialFrameworkFactory(question_part=question_part)
    factories.InitialThemeFactory(key="A", framework=framework)
    factories.InitialThemeFactory(key="B", framework=framework)

    import_all_theme_mappings_from_jsonl(
        question_part=question_part,
        bucket_name="test-bucket",
        question_part_folder_key="app_data/CON1/outputs/mapping/2025-04-01/question_part_1/",
        batch_size=2,
    )

    # TODO - improve this, but it works for now!
    time.sleep(5)
    theme_mappings = ThemeMapping.objects.all().order_by("created_at")
    assert theme_mappings.count() == 4
    assert theme_mappings[0].answer.question_part.id == question_part.id
    assert theme_mappings[0].theme.key == "A"
    assert theme_mappings[3].answer.question_part.id == question_part.id
    assert theme_mappings[3].theme.key == "B"


@pytest.mark.django_db
def test_import_sentiment_mappings():
    sentimentmapping_data = [
        b'{"themefinder_id":1,"sentiment":"AGREEMENT"}',
        b'{"themefinder_id":2,"sentiment":"DISAGREEMENT"}',
        b'{"themefinder_id":4,"sentiment":"UNCLEAR"}',
    ]
    question_part = factories.FreeTextQuestionPartFactory()
    consultation = question_part.question.consultation
    respondent_1 = factories.RespondentFactory(
        themefinder_respondent_id=1, consultation=consultation
    )
    respondent_2 = factories.RespondentFactory(
        themefinder_respondent_id=2, consultation=consultation
    )
    respondent_3 = factories.RespondentFactory(
        themefinder_respondent_id=3, consultation=consultation
    )
    respondent_4 = factories.RespondentFactory(
        themefinder_respondent_id=4, consultation=consultation
    )
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_1)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_2)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_3)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_4)

    import_sentiment_mappings(
        question_part=question_part, sentimentmapping_data=sentimentmapping_data
    )
    sentiment_mappings = SentimentMapping.objects.filter(
        answer__question_part=question_part
    ).order_by("answer__respondent__themefinder_respondent_id")
    assert sentiment_mappings.count() == 3
    assert sentiment_mappings[0].position == SentimentMapping.Position.AGREEMENT
    assert sentiment_mappings[2].position == SentimentMapping.Position.UNCLEAR


@pytest.mark.django_db
def test_import_all_sentiment_mappings_from_jsonl(mock_consultation_input_objects):
    question_part = factories.FreeTextQuestionPartFactory()
    consultation = question_part.question.consultation
    respondent_1 = factories.RespondentFactory(
        themefinder_respondent_id=1, consultation=consultation
    )
    respondent_2 = factories.RespondentFactory(
        themefinder_respondent_id=2, consultation=consultation
    )
    respondent_3 = factories.RespondentFactory(
        themefinder_respondent_id=3, consultation=consultation
    )
    respondent_4 = factories.RespondentFactory(
        themefinder_respondent_id=4, consultation=consultation
    )
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_1)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_2)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_3)
    factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent_4)

    import_all_sentiment_mappings_from_jsonl(
        question_part=question_part,
        bucket_name="test-bucket",
        question_part_folder_key="app_data/CON1/outputs/mapping/2025-04-01/question_part_1/",
        batch_size=2,
    )
    # TODO - improve this, but it works for now!
    time.sleep(5)
    sentiment_mappings = SentimentMapping.objects.all().order_by("created_at")
    assert sentiment_mappings.count() == 3
    assert sentiment_mappings[0].position == SentimentMapping.Position.AGREEMENT
    assert sentiment_mappings[2].position == SentimentMapping.Position.UNCLEAR
