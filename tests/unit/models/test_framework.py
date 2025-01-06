from consultation_analyser.factories import UserFactory, ConsultationFactory, QuestionFactory, AnswerFactory, QuestionPartFactory, RespondentFactory
from consultation_analyser.consultations import models
from consultation_analyser import factories

def set_up() -> models.QuestionPart:
    question_part = QuestionPartFactory(type=models.QuestionPart.QuestionType.FREE_TEXT)
    consultation = question_part.question.consultation
    for i in range(5):
        respondent = RespondentFactory(consultation=consultation)
        AnswerFactory(question_part=question_part, respondent=respondent)
    return question_part


def set_up_initial_pipeline(question_part: models.QuestionPart) -> models.Framework:
    theme_generation_run = factories.ExecutionRunFactory(type=models.ExecutionRun.TaskType.THEME_GENERATION)
    first_framework = factories.FrameworkFactory(execution_run=theme_generation_run, question_part=question_part)
    # No user or precursor, as this is AI generated
    models.Theme(name="Theme X", framework=first_framework)
    models.Theme(name="Theme Y", framework=first_framework)
    return first_framework






def test_theme_framework():
    question_part = set_up()
    first_framework = set_up_initial_pipeline(question_part)
    assert first_framework.themes.count() == 2
    assert first_framework.themes.first().name == "Theme X"
    assert first_framework.themes.last().name == "Theme Y"
    assert first_framework.theme_mapping.count() == 0

    # Now amend the themes in the first framework
    framework_2a = factories.FrameworkFactory(precursor=first_framework)

