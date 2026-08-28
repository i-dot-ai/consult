from unittest.mock import patch

import boto3
import pytest
from django.core.management import call_command
from moto import mock_aws


class TestPrepareS3:
    @pytest.mark.django_db
    @mock_aws
    @patch("consultations.management.commands.prepare_s3.HostingEnvironment")
    def test_deletes_existing_data_before_seeding(self, mock_hosting_env, settings):
        mock_hosting_env.is_dev.return_value = True
        settings.AWS_BUCKET_NAME = "test-bucket"

        conn = boto3.resource("s3", region_name="eu-west-2")
        conn.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        # Pre-seed a stale object that should be cleaned up
        s3_client = boto3.client("s3", region_name="eu-west-2")
        s3_client.put_object(
            Bucket="test-bucket",
            Key="app_data/consultations/old-consultation/inputs/respondents.jsonl",
            Body="stale data",
        )

        call_command("prepare_s3")

        bucket = conn.Bucket("test-bucket")
        keys = [obj.key for obj in bucket.objects.all()]

        assert not any("old-consultation" in k for k in keys)
        assert any("dummy-s3-only/" in k for k in keys)

    @pytest.mark.django_db
    @mock_aws
    @patch("consultations.management.commands.prepare_s3.HostingEnvironment")
    def test_seeds_s3_with_data_for_each_stage(self, mock_hosting_env, settings):
        mock_hosting_env.is_dev.return_value = True
        settings.AWS_BUCKET_NAME = "test-bucket"

        conn = boto3.resource("s3", region_name="eu-west-2")
        conn.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        call_command("prepare_s3")

        bucket = conn.Bucket("test-bucket")
        keys = [obj.key for obj in bucket.objects.all()]

        # S3-only consultation has input data
        assert any("dummy-s3-only/inputs/respondents.jsonl" in k for k in keys)
        assert any("dummy-s3-only/inputs/question_part_1/question.json" in k for k in keys)

        # Setup consultation has input data
        assert any("dummy-setup/inputs/respondents.jsonl" in k for k in keys)
        assert any("dummy-setup/inputs/question_part_1/question.json" in k for k in keys)

        # Starting finalising themes has input data, clustered themes and candidate theme mappings
        assert any("dummy-start-finalising-themes/inputs/respondents.jsonl" in k for k in keys)
        assert any(
            "dummy-start-finalising-themes/inputs/question_part_1/question.json" in k for k in keys
        )
        assert any(
            "dummy-start-finalising-themes/outputs/sign_off/" in k and "clustered_themes.json" in k
            for k in keys
        )
        assert any(
            "dummy-start-finalising-themes/outputs/mapping/" in k and "mapping.jsonl" in k
            for k in keys
        )

        # Finished finalising themes has input data, clustered themes and candidate theme mappings
        assert any("dummy-finished-finalising-themes/inputs/respondents.jsonl" in k for k in keys)
        assert any(
            "dummy-finished-finalising-themes/inputs/question_part_1/question.json" in k
            for k in keys
        )
        assert any(
            "dummy-finished-finalising-themes/outputs/sign_off/" in k
            and "clustered_themes.json" in k
            for k in keys
        )
        assert any(
            "dummy-finished-finalising-themes/outputs/mapping/" in k and "mapping.jsonl" in k
            for k in keys
        )

        # Analysis has all the above and mapping outputs
        assert any("dummy-analysis/inputs/respondents.jsonl" in k for k in keys)
        assert any("dummy-analysis/inputs/question_part_1/question.json" in k for k in keys)
        assert any(
            "dummy-analysis/outputs/sign_off/" in k and "clustered_themes.json" in k for k in keys
        )
        assert any("dummy-analysis/outputs/mapping/" in k and "mapping.jsonl" in k for k in keys)
        assert any("dummy-analysis/outputs/mapping/" in k and "themes.json" in k for k in keys)
        assert any("dummy-analysis/outputs/mapping/" in k and "sentiment.jsonl" in k for k in keys)
        assert any(
            "dummy-analysis/outputs/mapping/" in k and "detail_detection.jsonl" in k for k in keys
        )

    @pytest.mark.django_db
    @mock_aws
    @patch("consultations.management.commands.prepare_s3.HostingEnvironment")
    def test_skips_on_preprod(self, mock_hosting_env, settings):
        mock_hosting_env.is_dev.return_value = False
        settings.AWS_BUCKET_NAME = "test-bucket"

        conn = boto3.resource("s3", region_name="eu-west-2")
        conn.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        call_command("prepare_s3")

        bucket = conn.Bucket("test-bucket")
        keys = [obj.key for obj in bucket.objects.all()]
        assert len(keys) == 0

    @pytest.mark.django_db
    @mock_aws
    @patch("consultations.management.commands.prepare_s3.HostingEnvironment")
    def test_skips_on_local(self, mock_hosting_env, settings):
        mock_hosting_env.is_dev.return_value = False
        settings.AWS_BUCKET_NAME = "test-bucket"

        conn = boto3.resource("s3", region_name="eu-west-2")
        conn.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        call_command("prepare_s3")

        bucket = conn.Bucket("test-bucket")
        keys = [obj.key for obj in bucket.objects.all()]
        assert len(keys) == 0
