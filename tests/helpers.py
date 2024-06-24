import json
import re
from contextlib import contextmanager
from io import BytesIO
from unittest.mock import MagicMock, patch

import boto3
from botocore.response import StreamingBody
from django.core import mail


def sign_in(django_app, email):
    homepage = django_app.get("/")
    homepage.click("Sign in", index=0)

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = "invalid@example.com"
    login_page.form.submit()

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = email
    login_page.form.submit()

    sign_in_email = mail.outbox[0]

    assert sign_in_email.subject == "Sign in to Consult"
    url = re.search("(?P<url>https?://\\S+)", sign_in_email.body).group("url")

    successful_sign_in_page = django_app.get(url)
    homepage = successful_sign_in_page.form.submit().follow().follow()

    mail.outbox.clear()
    return homepage


@contextmanager
def mock_sagemaker(available=True):
    with patch("boto3.client") as mock_client:
        mock_sagemaker = MagicMock()
        mock_client.return_value = mock_sagemaker

        fake_response = """{"short_description": "Personal preference", \
                            "summary": "Some preferred one, some another"}"""
        body_json = [{"generated_text": fake_response}]
        body_encoded = json.dumps(body_json).encode()
        body = StreamingBody(BytesIO(body_encoded), len(body_encoded))
        mock_resp = {"Body": body}

        mock_sagemaker.invoke_endpoint.return_value = mock_resp

        if available:
            mock_sagemaker.describe_endpoint.return_value = {
                "EndpointName": "test-endpoint",
                "EndpointStatus": "InService",
            }
        else:
            mock_sagemaker.describe_endpoint.side_effect = [
                boto3.exceptions.botocore.exceptions.ClientError(
                    error_response={
                        "Error": {
                            "Code": "ValidationException",
                            "Message": "Could not find endpoint",
                        }
                    },
                    operation_name="describe_endpoint",
                ),
                {"EndpointName": "test-endpoint", "EndpointStatus": "Creating"},
                {"EndpointName": "test-endpoint", "EndpointStatus": "InService"},
            ]

        yield mock_sagemaker
