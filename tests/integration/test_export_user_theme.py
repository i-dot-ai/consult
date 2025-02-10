import re
from unittest.mock import patch

import pytest
from django.urls import reverse

from consultation_analyser import factories
from consultation_analyser.consultations import models
from tests.helpers import sign_in


@pytest.mark.django_db
@patch("consultation_analyser.consultations.export_user_theme.boto3.client")
def test_export_user_theme(mock_boto_client, django_app):
    user = factories.UserFactory(is_staff=True)
    # Set up consultation with question and response
    consultation = factories.ConsultationFactory()
    consultation.users.add(user)
    question = factories.QuestionFactory(consultation=consultation)
    question_part = factories.FreeTextQuestionPartFactory(question=question)
    response = factories.FreeTextAnswerFactory(question_part=question_part)

    # Set up themes and theme mappings
    framework = factories.InitialFrameworkFactory(question_part=question_part)
    theme1 = factories.InitialThemeFactory(framework=framework)
    theme2 = factories.InitialThemeFactory(framework=framework)
    theme3 = factories.InitialThemeFactory(framework=framework)

    factories.ThemeMappingFactory(
        answer=response, theme=theme1, stance=models.ThemeMapping.Stance.POSITIVE
    )
    factories.ThemeMappingFactory(
        answer=response, theme=theme2, stance=models.ThemeMapping.Stance.NEGATIVE
    )

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
    review_response_page.form.submit()

    # Call the method
    export_url = reverse("export_consultation_theme_audit", args=(consultation.id,))

    export_page = django_app.get(export_url)
    export_page.form["s3_key"] = "test_key"
    new_page = export_page.form.submit().follow()
    assert "Consultation theme audit exported" in new_page

    # Test the results
    mock_boto_client.assert_called_once_with("s3")
    mock_boto_client.return_value.put_object.assert_called_once()

    generated_csv = mock_boto_client.return_value.put_object.call_args[1]["Body"]

    # TODO: convert to csv and read as dict
    assert len(re.findall(theme1.name, generated_csv)) == 1
    assert len(re.findall(theme2.name, generated_csv)) == 2
    assert len(re.findall(theme3.name, generated_csv)) == 1
