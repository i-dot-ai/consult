import pytest

from consultation_analyser.consultations.dummy_data import DummyConsultation
from consultation_analyser.consultations.models import Consultation, Question, Answer


@pytest.mark.django_db
def test_a_consultation_is_generated(settings):
    settings.DEBUG = True
    assert Consultation.objects.count() == 0

    DummyConsultation()

    assert Consultation.objects.count() == 1
    assert Question.objects.count() == 10
    assert Answer.objects.count() == 100


@pytest.mark.django_db
def test_the_tool_will_only_run_in_dev(settings):
    settings.DEBUG = False

    with pytest.raises(Exception, match=r"should only be run in development"):
        DummyConsultation()
