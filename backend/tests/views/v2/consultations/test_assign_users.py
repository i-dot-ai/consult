import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

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
    assert response.json() == {
        "added_count": 1,
        "non_existent_emails": [],
        "total_requested": 1,
    }
    assert consultation.users.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_v2_owner_assigns_multiple_users_and_reports_unknown_emails(
    client, non_staff_user, non_staff_user_token
):
    consultation = ConsultationFactory(created_by=non_staff_user)
    first_user = UserFactory(email="first@example.com")
    second_user = UserFactory(email="second@example.com")

    response = client.post(
        _url(consultation),
        data={
            "emails": [
                first_user.email,
                "missing@example.com",
                second_user.email,
                first_user.email,
            ]
        },
        content_type="application/json",
        headers=_auth(non_staff_user_token),
    )

    assert response.status_code == 201
    assert response.json() == {
        "added_count": 2,
        "non_existent_emails": ["missing@example.com"],
        "total_requested": 3,
    }
    assert set(consultation.users.values_list("id", flat=True)) == {
        first_user.id,
        second_user.id,
    }


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
