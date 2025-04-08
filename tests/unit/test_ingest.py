import pytest
from django.conf import settings

from consultation_analyser import factories
from consultation_analyser.consultations.models import (
    Answer,
    ExecutionRun,
    QuestionPart,
    Respondent,
    SentimentMapping,
    Theme,
    ThemeMapping,
)
from consultation_analyser.support_console.ingest import (
    get_themefinder_outputs_for_question,
    import_question_part_data,
    import_responses,
    import_theme_mappings_for_framework,
    import_themes,
)


@pytest.mark.django_db
def test_import_themes(refined_themes):
    question_part = factories.FreeTextQuestionPartFactory()
    import_themes(question_part=question_part, theme_data=refined_themes)
    imported_themes = Theme.objects.filter(framework__question_part=question_part)
    # Themes imported correctly
    assert imported_themes.count() == 5
    theme_a = imported_themes.get(key="A")
    assert theme_a.name == "Fair Trade Certification"
    assert (
        theme_a.description
        == "Ensuring ethical sourcing and supporting sustainable farming practises by requiring fair trade certification for all chocolate products."
    )
    assert {"A", "B", "C", "D", "E"} == set(imported_themes.values_list("key", flat=True))
    # Framework generated for themes, has the right type of execution run
    framework = theme_a.framework
    assert framework.execution_run.type == ExecutionRun.TaskType.THEME_GENERATION
    assert framework.theme_set.all().count() == 5


@pytest.mark.django_db
def test_import_theme_mappings_for_framework(refined_themes, mapping):
    # Populate with themes first
    question_part = factories.FreeTextQuestionPartFactory()
    consultation = question_part.question.consultation
    framework = import_themes(question_part=question_part, theme_data=refined_themes)

    import_theme_mappings_for_framework(framework=framework, list_mappings=mapping)
    # Check overall numbers
    all_respondents_for_consultation = Respondent.objects.filter(consultation=consultation)
    assert all_respondents_for_consultation.count() == 6
    answers_for_question_part = Answer.objects.filter(question_part=question_part)
    assert answers_for_question_part.count() == 6
    theme_mappings = ThemeMapping.objects.filter(answer__question_part=question_part)
    assert theme_mappings.count() == 9

    # Now check response 2 has been imported correctly
    respondent2 = all_respondents_for_consultation.get(themefinder_respondent_id=2)
    answer2 = answers_for_question_part.get(respondent=respondent2)
    assert answer2.text.startswith("Fair trade certification could")
    sentiment_mapping2 = SentimentMapping.objects.get(answer=answer2)
    assert sentiment_mapping2.position == SentimentMapping.Position.AGREEMENT
    theme_mappings2 = theme_mappings.filter(answer=answer2)
    assert theme_mappings2.count() == 2
    theme_a_mapping = theme_mappings2.get(theme__key="A")
    assert theme_a_mapping.stance == ThemeMapping.Stance.POSITIVE
    theme_c_mapping = theme_mappings2.get(theme__key="C")
    assert theme_c_mapping.stance == ThemeMapping.Stance.NEGATIVE

    # Now check response 5 has been imported correctly
    respondent5 = all_respondents_for_consultation.get(themefinder_respondent_id=5)
    answer5 = answers_for_question_part.get(respondent=respondent5)
    assert answer5.text == "Meh."
    sentiment_mapping5 = SentimentMapping.objects.get(answer=answer5)
    assert sentiment_mapping5.position == SentimentMapping.Position.UNCLEAR
    theme_mappings5 = theme_mappings.filter(answer=answer5)
    assert theme_mappings5.count() == 1
    theme_e_mapping = theme_mappings5.get(theme__key="E")
    assert not theme_e_mapping.stance


@pytest.mark.django_db
def test_importing_for_different_questions(refined_themes, refined_themes2, mapping, mapping2):
    consultation = factories.ConsultationFactory()
    question1 = factories.QuestionFactory(consultation=consultation)
    question2 = factories.QuestionFactory(consultation=consultation)
    question_part1 = factories.FreeTextQuestionPartFactory(question=question1)
    question_part2 = factories.FreeTextQuestionPartFactory(question=question2)

    framework1 = import_themes(question_part=question_part1, theme_data=refined_themes)
    framework2 = import_themes(question_part=question_part2, theme_data=refined_themes2)
    import_theme_mappings_for_framework(framework=framework1, list_mappings=mapping)
    import_theme_mappings_for_framework(framework=framework2, list_mappings=mapping2)

    assert Respondent.objects.filter(consultation=consultation).count() == 7
    assert (
        Respondent.objects.filter(consultation=consultation)
        .filter(themefinder_respondent_id=6)
        .exists()
    )
    assert Answer.objects.filter(question_part=question_part2).count() == 2


def test_get_themefinder_outputs_for_question(mock_s3_objects, monkeypatch):
    monkeypatch.setattr(settings, "AWS_BUCKET_NAME", "test-bucket")
    outputs = get_themefinder_outputs_for_question("folder/question_0/", "question")
    assert outputs.get("question") == "What do you think?"
    outputs = get_themefinder_outputs_for_question("folder/question_0/", "updated_mapping")
    assert outputs[1].get("response_id") == 1
    assert outputs[1].get("labels") == ["C", "D"]
    outputs = get_themefinder_outputs_for_question("folder/question_0/", "themes")
    assert len(outputs) == 5
    outputs = get_themefinder_outputs_for_question("folder/question_1/", "themes")
    assert len(outputs) == 3


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
