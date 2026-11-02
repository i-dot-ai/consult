from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import User
from factories import ConsultationFactory, UserFactory


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _url(consultation):
    return reverse("consultation-v2-assign-users", kwargs={"pk": consultation.id})


@pytest.mark.django_db
def test_v2_owner_assigns_single_user_by_email(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)
    user = UserFactory(email="new.user@example.com")

    response = client.post(
        _url(consultation),
        data={"emails": ["NEW.USER@EXAMPLE.COM"]},
        content_type="application/json",
        headers=_auth(non_staff_user_token),
    )

    assert response.status_code == 201
    assert response.json() == {"added_count": 1}
    assert consultation.users.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_v2_assign_users_logs_who_added_whom(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)
    user = UserFactory(email="new.user@example.com")

    with patch("consultations.api_v2.views.consultation.logger") as logger:
        client.post(
            _url(consultation),
            data={"emails": [user.email]},
            content_type="application/json",
            headers=_auth(non_staff_user_token),
        )

    logger.info.assert_called_once_with(
        "Added {added_emails} to consultation {consultation_id} by {actor}, "
        "creating accounts for {created_emails}",
        added_emails=[user.email],
        created_emails=[],
        consultation_id=str(consultation.id),
        actor=non_staff_user.email,
    )


@pytest.mark.django_db
def test_v2_assign_users_matches_an_account_whatever_its_case(
    client, non_staff_user, non_staff_user_token
):
    consultation = ConsultationFactory(created_by=non_staff_user)
    user = UserFactory(email="Mixed.Case@example.com")

    response = client.post(
        _url(consultation),
        data={"emails": ["mixed.case@example.com"]},
        content_type="application/json",
        headers=_auth(non_staff_user_token),
    )

    assert response.status_code == 201
    assert response.json() == {"added_count": 1}
    assert consultation.users.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_v2_owner_assigns_multiple_users_once_each(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)
    first_user = UserFactory(email="first@example.com")
    second_user = UserFactory(email="second@example.com")

    response = client.post(
        _url(consultation),
        data={"emails": [first_user.email, second_user.email, first_user.email]},
        content_type="application/json",
        headers=_auth(non_staff_user_token),
    )

    assert response.status_code == 201
    assert response.json() == {"added_count": 2}
    assert set(consultation.users.values_list("id", flat=True)) == {
        first_user.id,
        second_user.id,
    }


@pytest.mark.django_db
def test_v2_assign_users_creates_accounts_for_unknown_emails(
    client, non_staff_user, non_staff_user_token
):
    consultation = ConsultationFactory(created_by=non_staff_user)
    known_user = UserFactory(email="known@example.com")

    with patch("consultations.api_v2.views.consultation.logger") as logger:
        response = client.post(
            _url(consultation),
            data={"emails": [known_user.email, "missing@example.com", "Other@Example.com"]},
            content_type="application/json",
            headers=_auth(non_staff_user_token),
        )

    assert response.status_code == 201
    assert response.json() == {"added_count": 3}
    assert set(consultation.users.values_list("email", flat=True)) == {
        known_user.email,
        "missing@example.com",
        "other@example.com",
    }
    created = User.objects.get(email="other@example.com")
    assert created.is_staff is False
    assert created.is_superuser is False
    assert logger.info.call_args.kwargs["created_emails"] == [
        "missing@example.com",
        "other@example.com",
    ]


@pytest.mark.django_db
def test_v2_assign_users_adds_an_account_created_by_a_concurrent_request(
    client, non_staff_user, non_staff_user_token
):
    consultation = ConsultationFactory(created_by=non_staff_user)

    def create_user_after_someone_else_did(email):
        UserFactory(email=email)
        raise ValidationError({"email": ["User with this Email address already exists."]})

    with (
        patch.object(User.objects, "create_user", side_effect=create_user_after_someone_else_did),
        patch("consultations.api_v2.views.consultation.logger") as logger,
    ):
        response = client.post(
            _url(consultation),
            data={"emails": ["raced@example.com"]},
            content_type="application/json",
            headers=_auth(non_staff_user_token),
        )

    assert response.status_code == 201
    assert response.json() == {"added_count": 1}
    assert consultation.users.filter(email="raced@example.com").exists()
    assert logger.info.call_args.kwargs["created_emails"] == ["raced@example.com"]


@pytest.mark.django_db
def test_v2_superuser_assigns_user(client):
    superuser = UserFactory(is_staff=True, is_superuser=True)
    token = str(RefreshToken.for_user(superuser).access_token)
    consultation = ConsultationFactory()
    user = UserFactory()

    response = client.post(
        _url(consultation),
        data={"emails": [user.email]},
        content_type="application/json",
        headers=_auth(token),
    )

    assert response.status_code == 201
    assert consultation.users.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_v2_non_owner_cannot_assign_users(client):
    user = UserFactory(is_staff=False, is_superuser=False)
    token = str(RefreshToken.for_user(user).access_token)
    consultation = ConsultationFactory()
    consultation.users.add(user)
    user_to_assign = UserFactory()

    response = client.post(
        _url(consultation),
        data={"emails": [user_to_assign.email]},
        content_type="application/json",
        headers=_auth(token),
    )

    assert response.status_code == 403
    assert not consultation.users.filter(pk=user_to_assign.pk).exists()


@pytest.mark.django_db
def test_v2_staff_user_assigns_user(client):
    staff_user = UserFactory(is_staff=True, is_superuser=False)
    token = str(RefreshToken.for_user(staff_user).access_token)
    consultation = ConsultationFactory()
    user_to_assign = UserFactory()

    response = client.post(
        _url(consultation),
        data={"emails": [user_to_assign.email]},
        content_type="application/json",
        headers=_auth(token),
    )

    assert response.status_code == 201
    assert consultation.users.filter(pk=user_to_assign.pk).exists()


@pytest.mark.django_db
def test_v2_unauthenticated_user_cannot_assign_users(client):
    consultation = ConsultationFactory()

    response = client.post(
        _url(consultation),
        data={"emails": [UserFactory().email]},
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"emails": []},
        {"emails": ["not-an-email"]},
        {"email": "one@example.com"},
    ],
)
def test_v2_assign_users_rejects_invalid_payload(
    client, non_staff_user, non_staff_user_token, payload
):
    consultation = ConsultationFactory(created_by=non_staff_user)

    response = client.post(
        _url(consultation),
        data=payload,
        content_type="application/json",
        headers=_auth(non_staff_user_token),
    )

    assert response.status_code == 400
