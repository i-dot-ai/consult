import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import QuestionPart
from tests.helpers import sign_in


@pytest.mark.django_db
def test_deleting_consultation_question_parts_via_support(django_app):
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
    delete_confirmation_page = consultations_page.click("Delete this question part")

    # Confirm the delete question page URL is correct
    expected_url = (
        f"/support/consultations/{consultation.id}/question-parts/{question_part.id}/delete/"
    )
    assert delete_confirmation_page.request.path == expected_url
    assert "Are you sure" in delete_confirmation_page

    # Cancel deletion
    delete_confirmation_page.form.submit("cancel_deletion")

    # Check question still exists
    assert QuestionPart.objects.filter(id=question_part.id).count() == 1

    # Go to consultation page in support
    consultations_page = django_app.get(f"/support/consultations/{consultation.id}/")

    # Click delete question
    delete_confirmation_page = consultations_page.click("Delete this question")

    # Confirm deletion
    delete_confirmation_page.form.submit("confirm_deletion")

    # Check question deleted
    assert QuestionPart.objects.filter(id=question.id).count() == 0
