import pytest

from consultation_analyser.consultations.models import Consultation


@pytest.mark.django_db
def test_initial_consultation_stage():
    consultation = Consultation()
    assert consultation.stage == Consultation.Stage.THEME_SIGN_OFF
