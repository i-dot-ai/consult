import pytest
from django.core.cache import cache

from consultation_analyser import factories
from tests.helpers import sign_in


@pytest.mark.django_db
def test_delete_default_cache(django_app):
    # Create and login an admin user
    user = factories.UserFactory(email="email@example.com", is_staff=True)
    sign_in(django_app, user.email)

    # Put stuff in the default cache
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"

    # Go to consultation page in support & click delete
    delete_cache_page = django_app.get("/support/cache/delete/")
    delete_confirmation_page = delete_cache_page.form.submit("delete_cache").follow()
    assert "Are you sure" in delete_confirmation_page

    # Confirm deletion
    delete_confirmation_page.form.submit("confirm_deletion")

    # Check cache has been deleted
    assert cache.get("test_key") is None
