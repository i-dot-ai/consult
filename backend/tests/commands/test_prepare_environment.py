from unittest.mock import patch

import boto3
import pytest
from django.core.management import call_command
from moto import mock_aws

from authentication.models import User
from consultations.models import Consultation


class TestPrepareEnvironment:
    @pytest.mark.django_db
    def test_does_not_reset_on_prod(self, settings):
        settings.ENVIRONMENT = "prod"

        Consultation.objects.create(title="Should survive", code="KEEP_ME")
        call_command("prepare_environment")

        assert Consultation.objects.filter(code="KEEP_ME").exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize("environment", ["dev", "preprod"])
    def test_resets_and_seeds_db(self, settings, environment):
        settings.ENVIRONMENT = environment

        Consultation.objects.create(title="Should be deleted", code="DELETE_ME")
        call_command("prepare_environment")

        # Old data is gone
        assert not Consultation.objects.filter(code="DELETE_ME").exists()

        # Consultations created at each stage
        assert Consultation.objects.filter(stage=Consultation.Stage.SETUP).exists()
        assert Consultation.objects.filter(stage=Consultation.Stage.THEME_SIGN_OFF).count() == 2
        assert Consultation.objects.filter(stage=Consultation.Stage.ANALYSIS).exists()

        # Admin user was created
        assert User.objects.filter(email="email@example.com", is_staff=True).exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize("environment", ["dev", "preprod"])
    @mock_aws
    @patch("factories.embed_text", return_value=[0.0] * 3072)
    @patch(
        "consultations.management.commands.prepare_s3.HostingEnvironment.is_production",
        return_value=False,
    )
    @patch(
        "consultations.management.commands.prepare_s3.HostingEnvironment.is_deployed",
        return_value=True,
    )
    def test_seeds_s3(self, _mock_deployed, _mock_prod, _mock_embed, settings, environment):
        settings.ENVIRONMENT = environment
        settings.AWS_BUCKET_NAME = "test-bucket"

        conn = boto3.resource("s3", region_name="eu-west-2")
        conn.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        call_command("prepare_environment")

        bucket = conn.Bucket("test-bucket")
        keys = [obj.key for obj in bucket.objects.all()]

        assert any("dummy-s3-only/" in k for k in keys)
        assert any("dummy-setup/" in k for k in keys)
        assert any("dummy-start-finalising-themes/" in k for k in keys)
        assert any("dummy-finished-finalising-themes/" in k for k in keys)
        assert any("dummy-analysis/" in k for k in keys)
