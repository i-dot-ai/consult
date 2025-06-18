import os
from unittest.mock import patch

import pytest

from consultation_analyser.consultations import models
from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml


@pytest.mark.django_db
@patch("consultation_analyser.hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_a_consultation_is_generated(settings):
    assert models.Consultation.objects.count() == 0
    create_dummy_consultation_from_yaml()
    assert models.Consultation.objects.count() == 1
    assert models.Question.objects.count() == 4



@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod"])
def test_the_tool_will_only_run_in_dev(environment):
    with patch.dict(os.environ, {"ENVIRONMENT": environment}):
        with pytest.raises(
            Exception, match=r"Dummy data generation should not be run in production"
        ):
            create_dummy_consultation_from_yaml()



@pytest.mark.django_db
def test_create_dummy_consultation_from_yaml():
    consultation = create_dummy_consultation_from_yaml(number_respondents=10)
    questions = models.Question.objects.filter(consultation=consultation)
    assert questions.count() == 4

    q1 = questions.get(number=1)
    assert q1.has_free_text
    assert q1.has_multiple_choice

    q1_themes = models.Theme.objects.filter(question=q1)
    assert len(q1_themes) == 2
    assert q1_themes.get(key="A").name == "Standardized framework"

    q3 = questions.get(number=3)
    assert not q3.has_free_text
    assert q3.has_multiple_choice
    assert q3.multiple_choice_options
