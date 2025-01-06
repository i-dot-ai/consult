import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_amend_framework():
    # set-up
    user = factories.UserFactory()
    question_part = factories.QuestionPartFactory()
    theme_generation_run = factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.THEME_GENERATION
    )
    framework_1 = factories.FrameworkFactory(
        execution_run=theme_generation_run, question_part=question_part, user=None
    )

    amended_framework = models.Framework.amend_framework(
        user=user, change_reason="I wanted to change the themes.", precursor=framework_1
    )
    # ID, precursor, user, change reason should all be updated.
    assert amended_framework.id != framework_1.id
    assert amended_framework.precursor == framework_1
    assert amended_framework.user == user
    assert amended_framework.change_reason == "I wanted to change the themes."
    # Other fields should not change - just copied over from the precursor.
    assert amended_framework.question_part == framework_1.question_part
