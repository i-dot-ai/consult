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

    assert models.Consultation.objects.count() == 4
    assert models.Question.objects.count() == 21

    setup = models.Consultation.objects.get(code="dummy-setup")
    assert setup.survey_import_status == models.Consultation.SurveyImportStatus.NOT_STARTED
    assert not setup.question_set.exists()

    generated = models.Consultation.objects.exclude(id=setup.id)
    assert not models.Question.objects.filter(consultation__in=generated, type__isnull=True).exists()
    assert not models.MultiChoiceAnswer.objects.filter(
        question__consultation__in=generated
    ).exists()
    assert not models.DemographicOption.objects.filter(consultation__in=generated).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod", "preprod"])
def test_the_tool_will_only_run_in_dev(environment):
    with (
        patch.dict(os.environ, {"ENVIRONMENT": environment}),
        pytest.raises(Exception, match=r"Dummy data generation should not be run in production"),
    ):
        call_command(
            "generate_dummy_data",
            stdout=StringIO(),  # we'll ignore this
        )
