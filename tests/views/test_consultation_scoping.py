import pytest
from django.contrib.auth.models import Group
from django.http.response import Http404
from django.test import RequestFactory

from consultation_analyser.consultations.views import consultations
from consultation_analyser.factories import ConsultationFactory, UserFactory


@pytest.mark.django_db
def test_get_consultation_we_own(client):
    user = UserFactory()
    dash_access = Group.objects.get(name="Dashboard access")
    user.groups.add(dash_access)
    user.save()
    consultation_we_own = ConsultationFactory()
    consultation_we_own.users.add(user)
    client.force_login(user)
    response = client.get(f"/consultations/{consultation_we_own.slug}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_consultation_we_do_not_own():
    user = UserFactory()
    consultation_we_do_not_own = ConsultationFactory()

    request_factory = RequestFactory()

    invalid_request = request_factory.get("/consultations/slug-does-not-matter-here/")
    invalid_request.user = user

    # rest of Django not around to catch 404 so we'll catch it ourselves
    with pytest.raises(Http404):
        consultations.show(invalid_request, consultation_slug=consultation_we_do_not_own.slug)
