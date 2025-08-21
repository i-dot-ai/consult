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
def test_export_user_theme(
    mock_boto_client, consultation, free_text_question, response_1, response_2, theme_a, theme_b, theme_c
):
    user = factories.UserFactory(is_staff=True)
    # Set up consultation with question and responses
    consultation.users.add(user)


    # Create response annotations with AI-assigned themes
    annotation1 = factories.ResponseAnnotationFactoryNoThemes(
        response=response_1,
        sentiment=models.ResponseAnnotation.Sentiment.AGREEMENT,
        human_reviewed=False,
    )
    annotation1.add_original_ai_themes([theme_b, theme_a])

    annotation2 = factories.ResponseAnnotationFactoryNoThemes(
        response=response_2,
        sentiment=models.ResponseAnnotation.Sentiment.UNCLEAR,
        human_reviewed=False,
    )
    annotation2.add_original_ai_themes([theme_c])

    with freeze_time("2023-01-01 12:00:00"):
        # Simulate user review - changing themes for response1
        annotation1.set_human_reviewed_themes([theme_a, theme_c], user)
        annotation1.mark_human_reviewed(user)

    # Call the method
    export_user_theme(free_text_question.id, "test_key")

    # Test the results
    mock_boto_client.return_value.put_object.assert_called_once()

    generated_csv = mock_boto_client.return_value.put_object.call_args[1]["Body"]
    exported_data = [row for row in csv.DictReader(generated_csv.splitlines(), delimiter=",")]

    # First answer has been audited and changed by user
    assert exported_data[0] == {
        "Response ID": str(response_1.respondent.themefinder_id),
        "Consultation": consultation.title,
        "Question number": str(free_text_question.number),
        "Question text": free_text_question.text,
        "Response text": response_1.free_text,
        "Response has been audited": str(True),
        "Original themes": get_sorted_theme_string([theme_b, theme_a]),
        "Current themes": get_sorted_theme_string([theme_a, theme_c]),
        "Position": "AGREEMENT",
        "Auditors": user.email,
        "First audited at": "2023-01-01 12:00:00+00:00",
    }

    # Second answer has not been audited
    assert exported_data[1] == {
        "Response ID": str(response_2.respondent.themefinder_id),
        "Consultation": consultation.title,
        "Question number": str(free_text_question.number),
        "Question text": free_text_question.text,
        "Response text": response_2.free_text,
        "Response has been audited": str(False),
        "Original themes": f"{theme_c.key}",
        "Current themes": f"{theme_c.key}",  # When not audited, current = original
        "Position": "UNCLEAR",
        "Auditors": "",
        "First audited at": "",
    }


@pytest.mark.django_db
@patch("django_rq.enqueue")
@patch("consultation_analyser.consultations.export_user_theme.boto3.client")
def test_start_export_job(
    mock_boto_client, mock_enqueue, consultation, free_text_question, response_1
):
    """Test that the export job is correctly enqueued"""
    from consultation_analyser.consultations.export_user_theme import export_user_theme_job

    user = factories.UserFactory(is_staff=True)
    # Set up consultation with question and response
    consultation.users.add(user)

    # Create at least one question with responses for the export to work

    # Create annotation so there's something to export
    annotation = factories.ResponseAnnotationFactoryNoThemes(
        response=response_1, sentiment=models.ResponseAnnotation.Sentiment.AGREEMENT
    )
    theme = factories.ThemeFactory(question=free_text_question)
    annotation.add_original_ai_themes([theme])

    # Mock the enqueue to capture the call
    mock_enqueue.return_value = None

    # Import and call the enqueue function directly
    from django_rq import enqueue

    enqueue(export_user_theme_job, free_text_question.id, "test_key")

    # Verify the job was enqueued
    mock_enqueue.assert_called_once_with(export_user_theme_job, free_text_question.id, "test_key")
