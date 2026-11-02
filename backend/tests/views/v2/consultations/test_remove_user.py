from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from factories import ConsultationFactory, UserFactory


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _url(consultation, user_id):
    return f"{reverse('consultation-v2-remove-user', kwargs={'pk': consultation.id})}?user_id={user_id}"


@pytest.mark.django_db
def test_v2_owner_removes_an_assigned_user(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)
    assigned_user = UserFactory()
    consultation.users.add(non_staff_user, assigned_user)

    response = client.delete(
        _url(consultation, assigned_user.id), headers=_auth(non_staff_user_token)
    )

    assert response.status_code == 204
    assert not consultation.users.filter(pk=assigned_user.pk).exists()
    assert consultation.users.filter(pk=non_staff_user.pk).exists()


@pytest.mark.django_db
def test_v2_staff_user_removes_an_assigned_user(client, staff_user_token):
    consultation = ConsultationFactory()
    assigned_user = UserFactory()
    consultation.users.add(assigned_user)

    response = client.delete(_url(consultation, assigned_user.id), headers=_auth(staff_user_token))

    assert response.status_code == 204
    assert not consultation.users.filter(pk=assigned_user.pk).exists()


@pytest.mark.django_db
def test_v2_assigned_user_cannot_remove_another(client, consultation, non_staff_user_token):
    other_user = UserFactory()
    consultation.users.add(other_user)

    response = client.delete(_url(consultation, other_user.id), headers=_auth(non_staff_user_token))

    assert response.status_code == 403
    assert consultation.users.filter(pk=other_user.pk).exists()


@pytest.mark.django_db
def test_v2_unrelated_user_cannot_remove(client, consultation):
    stranger = UserFactory(is_staff=False)
    token = str(RefreshToken.for_user(stranger).access_token)
    assigned_user = UserFactory()
    consultation.users.add(assigned_user)

    response = client.delete(_url(consultation, assigned_user.id), headers=_auth(token))

    assert response.status_code == 403
    assert consultation.users.filter(pk=assigned_user.pk).exists()


@pytest.mark.django_db
def test_v2_unauthenticated_user_cannot_remove(client, consultation):
    assigned_user = UserFactory()
    consultation.users.add(assigned_user)

    response = client.delete(_url(consultation, assigned_user.id))

    assert response.status_code == 401


@pytest.mark.django_db
def test_v2_remove_user_not_on_the_consultation_returns_404(
    client, non_staff_user, non_staff_user_token
):
    consultation = ConsultationFactory(created_by=non_staff_user)
    bystander = UserFactory()

    response = client.delete(_url(consultation, bystander.id), headers=_auth(non_staff_user_token))

    assert response.status_code == 404


@pytest.mark.django_db
def test_v2_remove_unknown_user_returns_404(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)

    response = client.delete(_url(consultation, 999999), headers=_auth(non_staff_user_token))

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("user_id", ["", "abc", "²"])
def test_v2_remove_user_requires_a_numeric_user_id(
    client, non_staff_user, non_staff_user_token, user_id
):
    consultation = ConsultationFactory(created_by=non_staff_user)

    response = client.delete(_url(consultation, user_id), headers=_auth(non_staff_user_token))

    assert response.status_code == 400
    assert "user_id" in response.json()


@pytest.mark.django_db
def test_v2_remove_user_logs_who_removed_whom(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)
    assigned_user = UserFactory()
    consultation.users.add(non_staff_user, assigned_user)

    with patch("consultations.api_v2.views.consultation.logger") as logger:
        client.delete(_url(consultation, assigned_user.id), headers=_auth(non_staff_user_token))

    logger.info.assert_called_once_with(
        "Removed {removed_email} from consultation {consultation_id} by {actor}",
        removed_email=assigned_user.email,
        consultation_id=str(consultation.id),
        actor=non_staff_user.email,
    )


@pytest.mark.django_db
def test_v2_remove_user_rejects_the_creator(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)
    consultation.users.add(non_staff_user)

    response = client.delete(
        _url(consultation, non_staff_user.id), headers=_auth(non_staff_user_token)
    )

    assert response.status_code == 400
    assert response.json() == {"user": "The person who created the consultation cannot be removed."}
    assert consultation.users.filter(pk=non_staff_user.pk).exists()
