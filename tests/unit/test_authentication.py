import pytest
from django.core.exceptions import ValidationError

from consultation_analyser.authentication.models import User


@pytest.mark.django_db
def test_create_valid_user():
    user = User.objects.create_user(email="email@example.com")
    assert user.id
    assert not user.is_staff


@pytest.mark.django_db
def test_create_user_with_invalid_email():
    with pytest.raises(ValidationError):
        User.objects.create_user(email="sdfdsf")


@pytest.mark.django_db
def test_create_user_with_duplicate_email():
    User.objects.create_user(email="email@example.com")

    with pytest.raises(ValidationError):
        # we don't respect case
        User.objects.create_user(email="EMAIL@example.com")
