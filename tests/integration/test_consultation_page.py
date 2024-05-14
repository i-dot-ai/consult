import pytest
from waffle.testutils import override_switch

from consultation_analyser.factories import ConsultationFactory, UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
@override_switch("FRONTEND_USER_LOGIN", True)
def test_consultation_page(django_app):
    user = UserFactory()
    consultation = ConsultationFactory(with_themes=True, user=user)

    sign_in(django_app, user.email)

    consultation_slug = consultation.slug
    question = consultation.section_set.first().question_set.first()
    homepage = django_app.get(f"/consultations/{consultation_slug}/")
    question_page = homepage.click("Question summary")

    assert "Question summary" in question_page
    assert f"{question.text}" in question_page
