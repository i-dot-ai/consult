# TODO - needed for fixing broken test below
# import csv
# from unittest.mock import patch

# import pytest
# from django.urls import reverse

# from consultation_analyser import factories
from consultation_analyser.consultations import models
from tests.helpers import sign_in


def get_sorted_theme_string(themes: list[models.Theme]) -> str:
    return ", ".join(sorted([theme.get_identifier() for theme in themes]))


# TODO - this test is flaky - needs to be fixed!
# @pytest.mark.django_db
# @patch("consultation_analyser.consultations.export_user_theme.boto3.client")
# def test_export_user_theme(mock_boto_client, django_app):
#     user = factories.UserFactory(is_staff=True)
#     # Set up consultation with question and response
#     consultation = factories.ConsultationFactory()
#     consultation.users.add(user)
#     question = factories.QuestionFactory(consultation=consultation)
#     question_part = factories.FreeTextQuestionPartFactory(question=question)
#     response = factories.FreeTextAnswerFactory(question_part=question_part)
#     response2 = factories.FreeTextAnswerFactory(question_part=question_part)

#     # Set up themes and theme mappings
#     framework = factories.InitialFrameworkFactory(question_part=question_part)
#     execution_run = factories.ExecutionRunFactory()
#     theme1 = factories.InitialThemeFactory(framework=framework)
#     theme2 = factories.InitialThemeFactory(framework=framework)
#     theme3 = factories.InitialThemeFactory(framework=framework)
#     factories.ThemeMappingFactory(
#         answer=response,
#         theme=theme1,
#         stance=models.ThemeMapping.Stance.POSITIVE,
#         execution_run=execution_run,
#     )
#     factories.ThemeMappingFactory(
#         answer=response,
#         theme=theme2,
#         stance=models.ThemeMapping.Stance.NEGATIVE,
#         execution_run=execution_run,
#     )
#     factories.ThemeMappingFactory(
#         answer=response2,
#         theme=theme3,
#         stance=models.ThemeMapping.Stance.POSITIVE,
#         execution_run=execution_run,
#     )

#     # Set up user changes
#     sign_in(django_app, user.email)
#     change_url = reverse(
#         "show_response",
#         args=(
#             consultation.slug,
#             question.slug,
#             response.id,
#         ),
#     )
#     review_response_page = django_app.get(change_url)
#     review_response_page.form["theme"] = [str(theme2.id), str(theme3.id)]
#     review_response_page.form.submit()

#     # Call the method
#     export_url = reverse("export_consultation_theme_audit", args=(consultation.id,))

#     export_page = django_app.get(export_url)
#     export_page.form["s3_key"] = "test_key"
#     new_page = export_page.form.submit().follow()
#     assert "Consultation theme audit exported" in new_page

#     # Test the results
#     mock_boto_client.assert_called_once_with("s3")
#     mock_boto_client.return_value.put_object.assert_called_once()

#     generated_csv = mock_boto_client.return_value.put_object.call_args[1]["Body"]
#     exported_data = [row for row in csv.DictReader(generated_csv.splitlines(), delimiter=",")]

#     # First answer has been audited and changed by user
#     assert exported_data[0] == {
#         "Consultation": consultation.title,
#         "Question number": str(question.number),
#         "Question text": question.text,
#         "Question part text": question_part.text,
#         "Response text": response.text,
#         "Response has been audited": "True",
#         "Original themes": get_sorted_theme_string([theme1, theme2]),
#         "Current themes": get_sorted_theme_string([theme2, theme3]),
#         "Auditors": user.email,
#     }

#     # Second answer has not been audited
#     assert exported_data[1] == {
#         "Consultation": consultation.title,
#         "Question number": str(question.number),
#         "Question text": question.text,
#         "Question part text": question_part.text,
#         "Response text": response2.text,
#         "Response has been audited": "False",
#         "Original themes": f"{theme3.get_identifier()}",
#         "Current themes": "",
#         "Auditors": "",
#     }
