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


