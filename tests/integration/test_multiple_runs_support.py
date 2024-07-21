import datetime
import pytest

from consultation_analyser.consultations import models
from consultation_analyser import factories
from tests.helpers import sign_in


@pytest.mark.django_db
def test_viewing_multiple_processing_runs_as_staff(django_app):
    user = factories.UserFactory(email="email@example.com", is_staff=True)
    sign_in(django_app, user.email)
    consultation = factories.ConsultationWithAnswersFactory()
    consultation.users.add(user)
    pr1 = factories.ProcessingRunFactory(consultation=consultation)
    pr2 = factories.ProcessingRunFactory(consultation=consultation)

    # Go to consultation in support - are processing runs shown?
    consultation_page = django_app.get(f"/support/consultations/{consultation.id}/")
    # TODO - sort out datetime/timezones
    # started_at_str = pr1.started_at.strftime("%-d %B %Y at %H:%M")
    # finished_at_str = pr2.finished_at.strftime("%-d %B %Y at %H:%M")
    # assert started_at_str in consultation_page
    # assert finished_at_str in consultation_page

    # Go to the first processing run in frontend
    frontend_first_run_page = consultation_page.click("View on frontend", index=1)
    assert frontend_first_run_page.request.url.endswith(f"/consultations/{consultation.slug}/runs/{pr1.slug}/")

    # Check we're going to the URL for that processing run
    question_summary = frontend_first_run_page.click("Question summary", index=0)
    assert pr1.slug in question_summary.request.url
    assert "question" in question_summary.request.url




