import pytest
from django.db import IntegrityError

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_uniqueness_consultation_slugs():
    factories.ConsultationFactory(name="My new consultation", slug="my-new-consultation")
    with pytest.raises(IntegrityError):
        factories.ConsultationFactory(name="My new consultation 2", slug="my-new-consultation")


@pytest.mark.django_db
def test_get_processing_run():
    # No processing run exists - return None
    consultation = factories.ConsultationFactory()
    assert not consultation.get_processing_run()

    pr1 = factories.ProcessingRunFactory(consultation=consultation)
    pr2 = factories.ProcessingRunFactory(consultation=consultation)

    # Default to getting latest processing run
    actual = consultation.get_processing_run()
    assert actual == pr2

    # Get specified processing run
    actual = consultation.get_processing_run(pr1.slug)
    assert actual == pr1

    # Error on passing in non-existent slug
    with pytest.raises(models.ProcessingRun.DoesNotExist):
        consultation.get_processing_run("invalid-slug")

    # Error if processing run slug for a diff consultation
    pr_diff_consultation = factories.ProcessingRunFactory()
    with pytest.raises(models.ProcessingRun.DoesNotExist):
        consultation.get_processing_run(pr_diff_consultation.slug)

