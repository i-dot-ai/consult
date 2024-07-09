import os
from unittest.mock import patch

import pytest

from consultation_analyser.consultations.dummy_data import create_dummy_data
from consultation_analyser.consultations.models import Answer, Consultation, Question


@pytest.mark.django_db
@patch("consultation_analyser.hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_a_consultation_is_generated(settings):
    assert Consultation.objects.count() == 0

    create_dummy_data()

    assert Consultation.objects.count() == 1
    assert Question.objects.count() == 10
    assert Answer.objects.count() >= 100


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod"])
def test_the_tool_will_only_run_in_dev(environment):
    with patch.dict(os.environ, {"ENVIRONMENT": environment}):
        with pytest.raises(
            Exception, match=r"Dummy data generation should not be run in production"
        ):
            create_dummy_data()


@pytest.mark.django_db
def test_answers_are_created_with_different_lengths_of_multiple_choice_options():
    create_dummy_data()

    questions = Question.objects.all()

    multichoice_stats = [q.multiple_choice_stats()[0] for q in questions]

    multiple_selections = [s.has_multiple_selections for s in multichoice_stats]

    assert multiple_selections.count(True) == 1
    assert multiple_selections.count(False) == 9
