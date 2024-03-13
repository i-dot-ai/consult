import pytest
from unittest.mock import patch
from io import StringIO
from consultation_analyser.consultations.models import Consultation

from django.core.management import call_command


@pytest.mark.django_db
@patch("consultation_analyser.hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_name_parameter_sets_consultation_name(mock_is_local):
    call_command(
        "generate_dummy_data",
        name="My special consultation",
        stdout=StringIO(),  # we'll ignore this
    )

    assert Consultation.objects.count() == 1
    assert Consultation.objects.first().name == "My special consultation"
    assert Consultation.objects.first().slug == "my-special-consultation"
