import os
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from consultations import models


@pytest.mark.django_db
@patch("hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_name_parameter_sets_consultation_name(mock_is_local):
    call_command(
        "generate_dummy_data",
        stdout=StringIO(),  # we'll ignore this
    )

    assert models.Consultation.objects.count() == 2
    assert models.Question.objects.count() == 8


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod"])
def test_the_tool_will_only_run_in_dev(environment):
    with patch.dict(os.environ, {"ENVIRONMENT": environment}):
        with pytest.raises(
            Exception, match=r"Dummy data generation should not be run in production"
        ):
            call_command(
                "generate_dummy_data",
                stdout=StringIO(),  # we'll ignore this
            )
