from unittest.mock import patch

import boto3
import pytest
from django.core.management import call_command
from moto import mock_aws

from authentication.models import User
from consultations.models import Consultation


class TestPrepareEnvironment:
    @pytest.mark.django_db
    @pytest.mark.parametrize("environment", ["prod", "preprod", "test", "", "unknown", "staging", "local"])
    def test_does_not_reset_on_non_dev(self, settings, environment):
        settings.ENVIRONMENT = environment

        Consultation.objects.create(title="Should survive", code="KEEP_ME")
        call_command("prepare_environment")

        assert Consultation.objects.filter(code="KEEP_ME").exists()

    @pytest.mark.django_db
    @mock_aws
    @patch("consultations.management.commands.prepare_s3.HostingEnvironment")
    @patch("factories.embed_text", return_value=[0.0] * 3072)
    def test_resets_and_seeds_db(self, _mock_embed, mock_hosting_env, settings):
        mock_hosting_env.is_production.return_value = False
        mock_hosting_env.is_preprod_environment.return_value = False
        mock_hosting_env.is_deployed.return_value = True

        settings.ENVIRONMENT = "dev"
        settings.AWS_BUCKET_NAME = "test-bucket"

        boto3.resource("s3", region_name="eu-west-2").create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        Consultation.objects.create(title="Should be deleted", code="DELETE_ME")
        call_command("prepare_environment")

        # Old data is gone
        assert not Consultation.objects.filter(code="DELETE_ME").exists()

        # Consultations created at each stage
        assert Consultation.objects.filter(stage=Consultation.Stage.SETUP).exists()
        assert Consultation.objects.filter(stage=Consultation.Stage.FINALISING_THEMES).exists()
        assert Consultation.objects.filter(stage=Consultation.Stage.ASSIGNING_THEMES).exists()
        assert Consultation.objects.filter(stage=Consultation.Stage.ANALYSIS).exists()

        # Admin user was created
        assert User.objects.filter(email="admin@example.com", is_staff=True).exists()

    @pytest.mark.django_db
    @mock_aws
    @patch("consultations.management.commands.prepare_s3.HostingEnvironment")
    @patch("factories.embed_text", return_value=[0.0] * 3072)
    def test_seeds_s3(self, _mock_embed, mock_hosting_env, settings):
        mock_hosting_env.is_production.return_value = False
        mock_hosting_env.is_preprod_environment.return_value = False
        mock_hosting_env.is_deployed.return_value = True

        settings.ENVIRONMENT = "dev"
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
