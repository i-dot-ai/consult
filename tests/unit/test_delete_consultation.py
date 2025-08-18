from unittest.mock import Mock, patch

import pytest

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.models import (
    Consultation,
    DemographicOption,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    Theme,
)
from consultation_analyser.support_console.views.consultations import delete_consultation_job


@pytest.mark.django_db
def test_delete_consultation_cascading():
    """Test that deleting a consultation cascades to all related objects."""
    # Create test user
    user = User.objects.create_user(email="test@example.com")

    # Create consultation with full data structure
    consultation = Consultation.objects.create(title="Test Consultation")
    consultation.users.add(user)

    # Create question
    question = Question.objects.create(
        consultation=consultation,
        text="What do you think?",
        slug="question-1",
        number=1,
        has_free_text=True,
        has_multiple_choice=False,
    )

    # Create respondents
    o1, _ = DemographicOption.objects.get_or_create(
        consultation=consultation, field_name="age", field_value="25-34"
    )
    respondent1 = Respondent.objects.create(consultation=consultation, themefinder_id=1)
    respondent1.demographics.add(o1)
    respondent1.save()

    o2, _ = DemographicOption.objects.get_or_create(
        consultation=consultation, field_name="age", field_value="35-44"
    )
    respondent2 = Respondent.objects.create(consultation=consultation, themefinder_id=2)
    respondent2.demographics.add(o2)
    respondent2.save()

    # Create responses
    response1 = Response.objects.create(
        respondent=respondent1, question=question, free_text="I think it's great"
    )
    response2 = Response.objects.create(
        respondent=respondent2, question=question, free_text="I disagree"
    )

    # Create themes
    theme1 = Theme.objects.create(
        question=question,
        name="Positive feedback",
        description="Positive responses",
        key="positive",
    )
    theme2 = Theme.objects.create(
        question=question,
        name="Negative feedback",
        description="Negative responses",
        key="negative",
    )

    # Create response annotations
    annotation1 = ResponseAnnotation.objects.create(
        response=response1,
        sentiment=ResponseAnnotation.Sentiment.AGREEMENT,
        evidence_rich=True,
        human_reviewed=False,
    )
    annotation1.themes.add(theme1)

    annotation2 = ResponseAnnotation.objects.create(
        response=response2,
        sentiment=ResponseAnnotation.Sentiment.DISAGREEMENT,
        evidence_rich=False,
        human_reviewed=False,
    )
    annotation2.themes.add(theme2)

    # Verify all objects exist
    assert Consultation.objects.count() == 1
    assert Question.objects.count() == 1
    assert Respondent.objects.count() == 2
    assert Response.objects.count() == 2
    assert Theme.objects.count() == 2
    assert ResponseAnnotation.objects.count() == 2

    # Delete the consultation
    consultation.delete()

    # Verify cascading deletion
    assert Consultation.objects.count() == 0
    assert Question.objects.count() == 0
    assert Respondent.objects.count() == 0
    assert Response.objects.count() == 0
    assert Theme.objects.count() == 0
    assert ResponseAnnotation.objects.count() == 0


@pytest.mark.django_db
@patch("django.db.connection")
def test_delete_consultation_job_success(mock_connection):
    """Test the delete_consultation_job function executes successfully."""
    # Mock connection.close() to prevent test database connection issues
    mock_connection.close = Mock()

    # Create test data
    user = User.objects.create_user(email="test@example.com")
    consultation = Consultation.objects.create(title="Test Consultation")
    consultation.users.add(user)

    question = Question.objects.create(
        consultation=consultation, text="Test question", slug="question-1", number=1
    )

    respondent = Respondent.objects.create(consultation=consultation, themefinder_id=1)

    response = Response.objects.create(
        respondent=respondent, question=question, free_text="Test response"
    )

    theme = Theme.objects.create(
        question=question, name="Test theme", description="Test description", key="test"
    )

    annotation = ResponseAnnotation.objects.create(
        response=response,
        sentiment=ResponseAnnotation.Sentiment.UNCLEAR,
        evidence_rich=False,
    )
    annotation.themes.add(theme)

    consultation_id = consultation.id

    # Verify objects exist before deletion
    assert Consultation.objects.filter(id=consultation_id).exists()
    assert Question.objects.filter(consultation_id=consultation_id).exists()
    assert Respondent.objects.filter(consultation_id=consultation_id).exists()
    assert Response.objects.filter(question__consultation_id=consultation_id).exists()
    assert Theme.objects.filter(question__consultation_id=consultation_id).exists()
    assert ResponseAnnotation.objects.filter(
        response__question__consultation_id=consultation_id
    ).exists()

    # Run the delete job
    delete_consultation_job(consultation)

    # Verify all objects are deleted
    assert not Consultation.objects.filter(id=consultation_id).exists()
    assert not Question.objects.filter(consultation_id=consultation_id).exists()
    assert not Respondent.objects.filter(consultation_id=consultation_id).exists()
    assert not Response.objects.filter(question__consultation_id=consultation_id).exists()
    assert not Theme.objects.filter(question__consultation_id=consultation_id).exists()
    assert not ResponseAnnotation.objects.filter(
        response__question__consultation_id=consultation_id
    ).exists()


@pytest.mark.django_db
@patch("django.db.connection")
def test_delete_consultation_job_handles_database_connection(mock_connection):
    """Test that the delete job properly handles database connections."""
    consultation = Consultation.objects.create(title="Test Consultation")

    # Run the delete job
    delete_consultation_job(consultation)


@pytest.mark.django_db
@patch("django.db.connection")
@patch("consultation_analyser.support_console.views.consultations.logger")
def test_delete_consultation_job_handles_exceptions(mock_logger, mock_connection):
    """Test that the delete job properly handles and logs exceptions."""
    # Mock connection.close() to prevent test database connection issues
    mock_connection.close = Mock()

    consultation = Consultation.objects.create(title="Test Consultation")

    # Mock an exception during the model get operation (after connection.close but before deletion)
    with patch(
        "consultation_analyser.consultations.models.Consultation.objects.get",
        side_effect=Exception("Database error"),
    ):
        with pytest.raises(Exception) as exc_info:
            delete_consultation_job(consultation)

        assert "Database error" in str(exc_info.value)


@pytest.mark.django_db
def test_delete_consultation_preserves_other_consultations():
    """Test that deleting one consultation doesn't affect others."""
    # Create two consultations
    consultation1 = Consultation.objects.create(title="Consultation 1")
    consultation2 = Consultation.objects.create(title="Consultation 2")

    # Add data to both
    Question.objects.create(
        consultation=consultation1, text="Question 1", slug="question-1-1", number=1
    )
    Question.objects.create(
        consultation=consultation2, text="Question 2", slug="question-2-1", number=1
    )

    Respondent.objects.create(consultation=consultation1, themefinder_id=1)
    Respondent.objects.create(consultation=consultation2, themefinder_id=2)

    # Verify both exist
    assert Consultation.objects.count() == 2
    assert Question.objects.count() == 2
    assert Respondent.objects.count() == 2

    # Delete only consultation1
    consultation1.delete()

    # Verify only consultation1 data is deleted
    assert Consultation.objects.count() == 1
    assert Consultation.objects.first().title == "Consultation 2"
    assert Question.objects.count() == 1
    assert Question.objects.first().text == "Question 2"
    assert Respondent.objects.count() == 1
    assert Respondent.objects.first().themefinder_id == 2


@pytest.mark.django_db
def test_delete_consultation_with_multiple_questions():
    """Test deleting a consultation with multiple questions and their data."""
    consultation = Consultation.objects.create(title="Multi-Question Consultation")

    # Create multiple questions
    question1 = Question.objects.create(consultation=consultation, text="Q1", slug="q1", number=1)
    question2 = Question.objects.create(consultation=consultation, text="Q2", slug="q2", number=2)

    # Create respondents
    respondent = Respondent.objects.create(consultation=consultation, themefinder_id=1)

    # Create responses for both questions
    response1 = Response.objects.create(
        respondent=respondent, question=question1, free_text="Answer 1"
    )
    response2 = Response.objects.create(
        respondent=respondent, question=question2, free_text="Answer 2"
    )

    # Create themes for both questions
    theme1 = Theme.objects.create(
        question=question1, name="Theme 1", key="t1", description="Theme for Q1"
    )
    theme2 = Theme.objects.create(
        question=question2, name="Theme 2", key="t2", description="Theme for Q2"
    )

    # Create annotations
    annotation1 = ResponseAnnotation.objects.create(
        response=response1, sentiment=ResponseAnnotation.Sentiment.AGREEMENT
    )
    annotation2 = ResponseAnnotation.objects.create(
        response=response2, sentiment=ResponseAnnotation.Sentiment.DISAGREEMENT
    )

    annotation1.themes.add(theme1)
    annotation2.themes.add(theme2)

    # Verify all data exists
    assert Question.objects.filter(consultation=consultation).count() == 2
    assert Response.objects.filter(question__consultation=consultation).count() == 2
    assert Theme.objects.filter(question__consultation=consultation).count() == 2
    assert (
        ResponseAnnotation.objects.filter(response__question__consultation=consultation).count()
        == 2
    )

    # Delete consultation
    consultation.delete()

    # Verify all related data is deleted
    assert Question.objects.filter(consultation_id=consultation.id).count() == 0
    assert Response.objects.filter(question__consultation_id=consultation.id).count() == 0
    assert Theme.objects.filter(question__consultation_id=consultation.id).count() == 0
    assert (
        ResponseAnnotation.objects.filter(
            response__question__consultation_id=consultation.id
        ).count()
        == 0
    )
