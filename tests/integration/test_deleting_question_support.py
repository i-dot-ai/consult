import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import Question
from tests.helpers import sign_in


@pytest.mark.django_db
def test_deleting_consultation_questions_via_support(django_app):
    question_part = factories.FreeTextQuestionPartFactory()
    question = question_part.question
    consultation = question.consultation

    # given I am an admin user
    user = factories.UserFactory(email="email@example.com", is_staff=True)
    consultation.users.add(user)

    sign_in(django_app, user.email)

    # Go to consultation page in support
    consultations_page = django_app.get(f"/support/consultations/{consultation.id}/")

    # Click delete question
    delete_confirmation_page = consultations_page.click("Delete this question")

    # Confirm the delete question page URL is correct
    expected_url = f"/support/consultations/{consultation.id}/questions/{question.id}/delete/"
    assert delete_confirmation_page.request.path == expected_url
    assert "Are you sure you want to delete the question" in delete_confirmation_page

    # Confirm deletion
    delete_confirmation_page.form.submit("confirm_deletion")

    # Check question deleted
    assert Question.objects.filter(id=question.id).count() == 0
