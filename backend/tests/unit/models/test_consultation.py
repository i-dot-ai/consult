import pytest

from consultations.models import Consultation
from factories import ConsultationFactory, UserFactory


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


def test_consultation_running_job_choices():
    assert Consultation.RunningJob.FIND_THEMES == "find-themes"
    assert Consultation.RunningJob.ASSIGN_THEMES == "assign-themes"
    assert Consultation.RunningJob.DELETING == "deleting"


def test_initial_consultation_created_by_is_none():
    consultation = Consultation()
    assert consultation.created_by is None


@pytest.mark.django_db
def test_consultation_created_by_can_be_set():
    user = UserFactory()
    consultation = ConsultationFactory(created_by=user)
    assert consultation.created_by == user


@pytest.mark.django_db
def test_consultation_created_by_reverse_accessor():
    user = UserFactory()
    consultation = ConsultationFactory(created_by=user)
    assert consultation in user.owned_consultations.all()


@pytest.mark.django_db
def test_consultation_created_by_is_independent_of_users():
    """created_by (owner) and users (access list) are separate relationships."""
    owner = UserFactory()
    assigned_user = UserFactory()
    consultation = ConsultationFactory(created_by=owner)
    consultation.users.add(assigned_user)

    assert consultation.created_by == owner
    assert assigned_user in consultation.users.all()
    assert owner not in consultation.users.all()


@pytest.mark.django_db
def test_consultation_created_by_set_null_on_user_delete():
    """Deleting the owner sets created_by to None rather than deleting the consultation."""
    user = UserFactory()
    consultation = ConsultationFactory(created_by=user)
    user.delete()

    consultation.refresh_from_db()
    assert consultation.created_by is None


@pytest.mark.django_db
def test_multiple_consultations_owned_by_same_user():
    user = UserFactory()
    consultation_a = ConsultationFactory(created_by=user)
    consultation_b = ConsultationFactory(created_by=user)

    owned = list(user.owned_consultations.all())
    assert consultation_a in owned
    assert consultation_b in owned
