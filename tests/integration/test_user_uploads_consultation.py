import pytest
from django.conf import settings
from django.core import mail
from waffle.testutils import override_switch
from webtest import Upload

from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in

from consultation_analyser.pipeline.dummy_pipeline import save_themes_for_consultation


@pytest.mark.django_db
@override_switch("FRONTEND_USER_LOGIN", True)
def test_user_uploads_consultation(django_app):
    # given i am a user without a consultation
    user = UserFactory()

    # when I sign in
    consultations_page = sign_in(django_app, user.email)

    # and I click the link to upload
    upload_page = consultations_page.click("Upload a consultation")

    # then I should see an upload page
    assert "Upload a consultation" in upload_page

    with open(settings.BASE_DIR / "tests" / "examples" / "upload.json", "r") as f:
        binary_data = str.encode(f.read())

    # and when I provide my JSON and submit the form
    upload_page.form["consultation_json"] = Upload("consultation.json", binary_data, "application/json")
    success_page = upload_page.form.submit()

    # then I should see a success page
    assert "Consultation uploaded" in success_page

    # and when I visit the consultation again I should still see the success page
    consultation = user.consultation_set.first()
    django_app.get(f"/consultations/{consultation.slug}/")
    assert "Consultation uploaded" in success_page
