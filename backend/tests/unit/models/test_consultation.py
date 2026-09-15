import pytest

from consultations.models import Consultation


@pytest.mark.django_db
def test_initial_consultation_stage():
    consultation = Consultation()
    assert consultation.stage == Consultation.Stage.SETUP


def test_initial_consultation_data_source_is_none():
    consultation = Consultation()
    assert consultation.data_source is None


def test_consultation_data_source_choices():
    assert Consultation.DataSource.QUALTRICS == "qualtrics"
    assert Consultation.DataSource.CITIZEN_SPACE == "citizen-space"
