import pytest

from consultation_analyser.support_console.ingest import import_themes, import_theme_mappings_for_framework
from consultation_analyser import factories
from consultation_analyser.consultations.models import Consultation, QuestionPart, Theme, ExecutionRun, Framework, ThemeMapping, Answer, Respondent, SentimentMapping


@pytest.fixture
def refined_themes():
    refined_themes = [
        {
            "A": "Fair Trade Certification: Ensuring ethical sourcing and supporting sustainable farming practises by requiring fair trade certification for all chocolate products.",
            "B": "Sugar and Portion Sizing: Addressing public health concerns by reducing sugar content and implementing stricter portion size regulations for chocolate bars.",
            "C": "Transparent Labelling: Improving transparency by mandating clear and comprehensive labelling of ingredients, nutritional information, and potential allergens.",
            "D": "Environmental Impact: Introducing measures to minimise the environmental impact of chocolate production, such as reducing packaging waste and promoting eco-friendly practises.",
            "E": "No theme: whatever the description of no theme is",
        }
    ]
    return refined_themes


@pytest.fixture
def mapping():
    mapping = [
        {
            "response_id": 0,
            "response": "Implementing stricter portion size regulations for chocolate bars could help promote healthier eating habits and address obesity concerns.",
            "position": "agreement",
            "reasons": [
                "The response suggests that regulating portion sizes could encourage moderation and healthier snacking.",
            ],
            "labels": [
                "B",
            ],
            "stances": [
                "POSITIVE",
            ],
        },
        {
            "response_id": 1,
            "response": "Implementing comprehensive labelling requirements for chocolate products could overwhelm consumers with too much information.",
            "position": "disagreement",
            "reasons": [
                "The response expresses concern that detailed labelling requirements might be confusing or overwhelming for consumers.",
                "Transparent labelling aims to empower informed decisions, but could potentially have the opposite effect if not executed carefully.",
            ],
            "labels": ["C", "D"],
            "stances": ["NEGATIVE", "NEGATIVE"],
        },
        {
            "response_id": 2,
            "response": "Fair trade certification could improve the lives of cocoa farmers and promote sustainable agriculture while also increasing consumer trust in chocolate products.",
            "position": "agreement",
            "reasons": [
                "The response highlights the potential benefits of fair trade certification for cocoa farmers and the environment.",
                "It also suggests that fair trade certification could enhance consumer confidence in chocolate products.",
            ],
            "labels": ["A", "C"],
            "stances": ["POSITIVE", "NEGATIVE"],
        },
        {
            "response_id": 3,
            "response": "Strict regulations on chocolate production could lead to job losses and financial strain for small businesses in the industry.",
            "position": "disagreement",
            "reasons": [
                "Stricter rules might make it difficult for smaller companies to remain compliant and competitive.",
            ],
            "labels": ["C"],
            "stances": ["NEGATIVE"],
        },
        {
            "response_id": 4,
            "response": "Increased regulation of the chocolate industry could disproportionately impact women, who are more likely to consume these products.",
            "position": "agreement",
            "reasons": [
                "The response suggests that women might be more affected by changes in the chocolate industry due to their higher consumption rates.",
                "Regulations that raise prices or reduce availability could have a greater impact on female consumers.",
            ],
            "labels": ["A", "D"],
            "stances": ["POSITIVE", "NEGATIVE"],
        },
        {
            "response_id": 5,
            "response": "Meh.",
            "position": "unclear",
            "reasons": [
                "Response is too short",
            ],
            "labels": [
                "E",
            ],
            "stances": [
                "",
            ],
        },
    ]
    return mapping



@pytest.mark.django_db
def test_import_themes(refined_themes):
    question_part = factories.FreeTextQuestionPartFactory()
    import_themes(question_part=question_part, theme_data=refined_themes[0])
    imported_themes = Theme.objects.filter(framework__question_part=question_part)
    # Themes imported correctly
    assert imported_themes.count() == 5
    theme_a = imported_themes.get(key="A")
    assert theme_a.name == "Fair Trade Certification"
    assert theme_a.description == "Ensuring ethical sourcing and supporting sustainable farming practises by requiring fair trade certification for all chocolate products."
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
    framework = import_themes(question_part=question_part, theme_data=refined_themes[0])

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
    assert theme_a_mapping.reason == "The response highlights the potential benefits of fair trade certification for cocoa farmers and the environment."
    assert theme_a_mapping.stance == ThemeMapping.Stance.POSITIVE
    theme_c_mapping = theme_mappings2.get(theme__key="C")
    assert theme_c_mapping.reason == "It also suggests that fair trade certification could enhance consumer confidence in chocolate products."
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
    assert theme_e_mapping.reason == "Response is too short"
