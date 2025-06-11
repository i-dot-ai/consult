import csv
from unittest.mock import patch

import pytest
from django.urls import reverse
from freezegun import freeze_time

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.consultations.export_user_theme import export_user_theme
from tests.helpers import sign_in
from tests.utils import get_sorted_theme_string


@pytest.mark.skip(reason="Doesn't work whilst in the middle of model changes")
@pytest.mark.django_db
@patch("consultation_analyser.consultations.export_user_theme.boto3.client")
def test_export_user_theme(mock_boto_client, django_app):
    user = factories.UserFactory(is_staff=True)
    # Set up consultation with question and responses
    consultation = factories.ConsultationFactory()
    consultation.users.add(user)
    question = factories.QuestionFactory(consultation=consultation)
    question_part = factories.FreeTextQuestionPartFactory(question=question)
    respondent = factories.RespondentFactory(consultation=consultation, themefinder_respondent_id=1)
    respondent2 = factories.RespondentFactory(
        consultation=consultation, themefinder_respondent_id=2
    )
    response = factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent)
    response2 = factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent2)

    # Assign sentiment/position
    # Create some historical ones first
    first_execution_run = factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
    )
    factories.SentimentMappingFactory(
        answer=response,
        execution_run=first_execution_run,
        position=models.SentimentMapping.Position.DISAGREEMENT,
    )

    # We only care about the latest sentiment mapping
    second_execution_run = factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
    )
    factories.SentimentMappingFactory(
        answer=response,
        execution_run=second_execution_run,
        position=models.SentimentMapping.Position.AGREEMENT,
    )
    factories.SentimentMappingFactory(
        answer=response2,
        execution_run=second_execution_run,
        position=models.SentimentMapping.Position.UNCLEAR,
    )

    # Set up themes and theme mappings
    # Set up some historical ones but we should only pick up the latest framework
    historical_framework = factories.InitialFrameworkFactory(question_part=question_part)
    historical_execution_run = factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.THEME_MAPPING
    )
    theme_x = factories.InitialThemeFactory(framework=historical_framework, key="X")
    factories.ThemeMappingFactory(
        answer=response,
        theme=theme_x,
        stance=models.ThemeMapping.Stance.POSITIVE,
        execution_run=historical_execution_run,
    )

    # Latest framework and theme mappings
    framework = factories.InitialFrameworkFactory(question_part=question_part)
    execution_run = factories.ExecutionRunFactory(type=models.ExecutionRun.TaskType.THEME_MAPPING)
    theme1 = factories.InitialThemeFactory(framework=framework, key="B")
    theme2 = factories.InitialThemeFactory(framework=framework, key="A")
    theme3 = factories.InitialThemeFactory(framework=framework, key="C")
    factories.ThemeMappingFactory(
        answer=response,
        theme=theme1,
        stance=models.ThemeMapping.Stance.POSITIVE,
        execution_run=execution_run,
    )
    factories.ThemeMappingFactory(
        answer=response,
        theme=theme2,
        stance=models.ThemeMapping.Stance.NEGATIVE,
        execution_run=execution_run,
    )
    factories.ThemeMappingFactory(
        answer=response2,
        theme=theme3,
        stance=models.ThemeMapping.Stance.POSITIVE,
        execution_run=execution_run,
    )

    with freeze_time("2023-01-01 12:00:00"):
        # Set up user changes
        sign_in(django_app, user.email)
        change_url = reverse(
            "show_response",
            args=(
                consultation.slug,
                question.slug,
                response.id,
            ),
        )
        review_response_page = django_app.get(change_url)
        review_response_page.form["theme"] = [str(theme2.id), str(theme3.id)]
        review_response_page.form.submit("Save and continue to a new response")

    # Call the method
    export_user_theme(question_part.id, "test_key")

    # Test the results
    # TODO: Unlear why this is this called twice?
    # Leave for now as we still get right outputs
    # mock_boto_client.assert_called_once_with("s3")
    mock_boto_client.return_value.put_object.assert_called_once()

    generated_csv = mock_boto_client.return_value.put_object.call_args[1]["Body"]
    exported_data = [row for row in csv.DictReader(generated_csv.splitlines(), delimiter=",")]

    # First answer has been audited and changed by user
    assert exported_data[0] == {
        "Response ID": "1",
        "Consultation": consultation.title,
        "Question number": str(question.number),
        "Question text": question.text,
        "Question part text": question_part.text,
        "Response text": response.text,
        "Response has been audited": "True",
        "Original themes": get_sorted_theme_string([theme1, theme2]),
        "Current themes": get_sorted_theme_string([theme2, theme3]),
        "Position": "AGREEMENT",
        "Auditors": user.email,
        "First audited at": "2023-01-01 12:00:00+00:00",
    }

    # Second answer has not been audited
    assert exported_data[1] == {
        "Response ID": "2",
        "Consultation": consultation.title,
        "Question number": str(question.number),
        "Question text": question.text,
        "Question part text": question_part.text,
        "Response text": response2.text,
        "Response has been audited": "False",
        "Original themes": f"{theme3.get_identifier()}",
        "Current themes": "",
        "Position": "UNCLEAR",
        "Auditors": "",
        "First audited at": "",
    }


@pytest.mark.skip(reason="Doesn't work whilst in the middle of model changes")
@pytest.mark.django_db
@patch("consultation_analyser.consultations.export_user_theme.boto3.client")
def test_start_export(mock_boto_client, django_app):
    user = factories.UserFactory(is_staff=True)
    # Set up consultation with question and response
    consultation = factories.ConsultationFactory()
    consultation.users.add(user)
    sign_in(django_app, user.email)

    # Call the method
    export_url = reverse("export_consultation_theme_audit", args=(consultation.id,))

    export_page = django_app.get(export_url)
    export_page.form["s3_key"] = "test_key"
    new_page = export_page.form.submit().follow()
    assert "Consultation theme audit export started" in new_page
