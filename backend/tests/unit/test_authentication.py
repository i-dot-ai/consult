import pytest
from django.core.exceptions import ValidationError

from authentication.models import User


@pytest.mark.django_db
def test_create_valid_user():
    user = User.objects.create_user(email="admin@example.com")
    assert user.id
    assert not user.is_staff


@pytest.mark.django_db
def test_create_user_with_invalid_email():
    with pytest.raises(ValidationError):
        User.objects.create_user(email="sdfdsf")


@pytest.mark.django_db
def test_create_user_with_duplicate_email():
    User.objects.create_user(email="admin@example.com")

    with pytest.raises(ValidationError):
        # we don't respect case
        User.objects.create_user(email="ADMIN@example.com")


@pytest.mark.django_db
def test_create_user_idempotent():
    User.objects.create_user(email="admin@example.com")

    # no error thrown
    User.objects.create_user(email="admin@example.com", idempotent=True)

    assert User.objects.count() == 1


@pytest.mark.django_db
def test_saving_a_user_stores_the_email_in_lower_case():
    user = User(email="Mixed.Case@example.com")

    user.save()

    user.refresh_from_db()
    assert user.email == "mixed.case@example.com"


@pytest.mark.django_db
def test_create_user_stores_the_email_in_lower_case():
    user = User.objects.create_user(email="Mixed.Case@example.com")

    assert user.email == "mixed.case@example.com"


@pytest.mark.django_db
def test_filtering_by_email_ignores_case():
    user = User.objects.create_user(email="admin@example.com")

    assert User.objects.get(email="ADMIN@example.com") == user
