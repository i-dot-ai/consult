import django
import pytest

from consultation_analyser.factories import ConsultationFactory


@pytest.mark.django_db
def test_consultation_save_unique_slugs():
    consultation_title = "My First Consultation"
    slugified = "my-first-consultation"
    consultation = ConsultationFactory(title=consultation_title)
    assert consultation.slug == slugified
    another_consultation = ConsultationFactory(title=consultation_title)
    assert another_consultation.slug != consultation.slug
    assert another_consultation.slug == f"{slugified}-1"
    yet_another_consultation = ConsultationFactory(title=consultation_title)
    assert yet_another_consultation.slug != consultation.slug
    assert yet_another_consultation.slug == f"{slugified}-2"


@pytest.mark.django_db
def test_consultation_save_update_slugs():
    consultation_title = "My First Consultation"
    consultation = ConsultationFactory(title=consultation_title)
    assert consultation.slug == "my-first-consultation"
    consultation.title = "My Second Consultation"
    consultation.save()
    # New model doesn't update slug once set
    assert consultation.slug == "my-first-consultation"


@pytest.mark.django_db
def test_consultation_cant_save_long_title():
    with pytest.raises(django.db.utils.DataError) as excinfo:
        ConsultationFactory(title=("T" * 257))
    assert "value too long" in str(excinfo.value)


@pytest.mark.django_db
def test_consultation_save_long_title_twice():
    title = "T" * 256
    consultation = ConsultationFactory(title=title)
    assert consultation.slug == "t" * 250  # Truncated to 250 chars
    consultation2 = ConsultationFactory(title=title)
    assert consultation2.slug == f"{'t' * 250}-1"
