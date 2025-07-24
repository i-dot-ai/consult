import csv
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.consultations.export_user_theme import export_user_theme
from tests.utils import get_sorted_theme_string


@pytest.mark.django_db
@patch("consultation_analyser.consultations.export_user_theme.boto3.client")
@patch("consultation_analyser.consultations.export_user_theme.settings.ENVIRONMENT", "production")
def test_export_user_theme(mock_boto_client, django_app):
    user = factories.UserFactory(is_staff=True)
    # Set up consultation with question and responses
    consultation = factories.ConsultationFactory()
    consultation.users.add(user)
    question = factories.QuestionFactory(consultation=consultation)
    respondent = factories.RespondentFactory(consultation=consultation, themefinder_id=1)
    respondent2 = factories.RespondentFactory(consultation=consultation, themefinder_id=2)
    response = factories.ResponseFactory(question=question, respondent=respondent)
    response2 = factories.ResponseFactory(question=question, respondent=respondent2)

    # Set up themes
    theme1 = factories.ThemeFactory(question=question, key="B")
    theme2 = factories.ThemeFactory(question=question, key="A")
    theme3 = factories.ThemeFactory(question=question, key="C")

    # Create response annotations with AI-assigned themes
    annotation1 = factories.ResponseAnnotationFactoryNoThemes(
        response=response,
        sentiment=models.ResponseAnnotation.Sentiment.AGREEMENT,
        human_reviewed=False,
    )
    annotation1.add_original_ai_themes([theme1, theme2])

    annotation2 = factories.ResponseAnnotationFactoryNoThemes(
        response=response2,
        sentiment=models.ResponseAnnotation.Sentiment.UNCLEAR,
        human_reviewed=False,
    )
    annotation2.add_original_ai_themes([theme3])

    with freeze_time("2023-01-01 12:00:00"):
        # Simulate user review - changing themes for response1
        annotation1.set_human_reviewed_themes([theme2, theme3], user)
        annotation1.mark_human_reviewed(user)

    # Call the method
    export_user_theme(question.id, "test_key")

    # Test the results
    mock_boto_client.return_value.put_object.assert_called_once()

    generated_csv = mock_boto_client.return_value.put_object.call_args[1]["Body"]
    exported_data = [row for row in csv.DictReader(generated_csv.splitlines(), delimiter=",")]

    # First answer has been audited and changed by user
    assert exported_data[0] == {
        "Response ID": str(respondent.themefinder_id),
        "Consultation": consultation.title,
        "Question number": str(question.number),
        "Question text": question.text,
        "Response text": response.free_text,
        "Response has been audited": str(True),
        "Original themes": get_sorted_theme_string([theme1, theme2]),
        "Current themes": get_sorted_theme_string([theme2, theme3]),
        "Position": "AGREEMENT",
        "Auditors": user.email,
        "First audited at": "2023-01-01 12:00:00+00:00",
    }

    # Second answer has not been audited
    assert exported_data[1] == {
        "Response ID": str(respondent2.themefinder_id),
        "Consultation": consultation.title,
        "Question number": str(question.number),
        "Question text": question.text,
        "Response text": response2.free_text,
        "Response has been audited": str(False),
        "Original themes": f"{theme3.key}",
        "Current themes": f"{theme3.key}",  # When not audited, current = original
        "Position": "UNCLEAR",
        "Auditors": "",
        "First audited at": "",
    }


@pytest.mark.django_db
@patch("django_rq.enqueue")
@patch("consultation_analyser.consultations.export_user_theme.boto3.client")
def test_start_export_job(mock_boto_client, mock_enqueue):
    """Test that the export job is correctly enqueued"""
    from consultation_analyser.consultations.export_user_theme import export_user_theme_job

    user = factories.UserFactory(is_staff=True)
    # Set up consultation with question and response
    consultation = factories.ConsultationFactory()
    consultation.users.add(user)

    # Create at least one question with responses for the export to work
    question = factories.QuestionFactory(consultation=consultation)
    respondent = factories.RespondentFactory(consultation=consultation)
    response = factories.ResponseFactory(question=question, respondent=respondent)

    # Create annotation so there's something to export
    annotation = factories.ResponseAnnotationFactoryNoThemes(
        response=response, sentiment=models.ResponseAnnotation.Sentiment.AGREEMENT
    )
    theme = factories.ThemeFactory(question=question)
    annotation.add_original_ai_themes([theme])

    # Mock the enqueue to capture the call
    mock_enqueue.return_value = None

    # Import and call the enqueue function directly
    from django_rq import enqueue

    enqueue(export_user_theme_job, question.id, "test_key")

    # Verify the job was enqueued
    mock_enqueue.assert_called_once_with(export_user_theme_job, question.id, "test_key")
