import pytest
from django.conf import settings

from data_pipeline.s3 import get_consultation_folders, get_question_folders

logger = settings.LOGGER


@pytest.mark.django_db
class TestGetQuestionFolders:
    def test_get_question_folders(self, minio_test_bucket, minio_client):
        """
        Test that get_question_folders correctly identifies question_part_N folders.

        Creates a realistic S3 structure with question folders and verifies only
        question_part_* folders are returned.
        """
        # Track objects we create for cleanup
        created_keys = []

        try:
            # Setup: Create test S3 objects
            test_objects = [
                "app_data/consultations/test/inputs/question_part_1/question.json",
                "app_data/consultations/test/inputs/question_part_1/responses.jsonl",
                "app_data/consultations/test/inputs/question_part_2/question.json",
                "app_data/consultations/test/inputs/question_part_2/responses.jsonl",
                "app_data/consultations/test/inputs/other_file.txt",
            ]

            for key in test_objects:
                minio_client.put_object(
                    Bucket=minio_test_bucket,
                    Key=key,
                    Body=b"test content"
                )
                created_keys.append(key)

            # Execute: Call the function under test
            result = get_question_folders(
                "app_data/consultations/test/inputs/",
                minio_test_bucket
            )

            # Verify: Check results
            expected = [
                "app_data/consultations/test/inputs/question_part_1/",
                "app_data/consultations/test/inputs/question_part_2/",
            ]
            assert sorted(result) == sorted(expected)

        finally:
            # Cleanup: Delete all objects we created
            for key in created_keys:
                try:
                    minio_client.delete_object(
                        Bucket=minio_test_bucket,
                        Key=key
                    )
                except Exception as e:
                    logger.warning("Failed to cleanup object {key}: {e}", key=key, e=e)


@pytest.mark.django_db
class TestGetConsultationFolders:
    def test_get_consultation_folders(self, minio_test_bucket, minio_client):
        """
        Test that get_consultation_folders extracts unique consultation codes.

        Creates multiple S3 objects across different consultation folders and verifies
        the function correctly extracts the unique consultation codes from the paths.
        """
        # Track objects we create for cleanup
        created_keys = []

        try:
            # Setup: Create test S3 structure with multiple consultations
            test_objects = [
                "app_data/consultations/healthcare-2024/inputs/question_part_1/question.json",
                "app_data/consultations/healthcare-2024/outputs/sign_off/2024-01-10/clustered_themes.json",
                "app_data/consultations/transport-2024/inputs/question_part_1/responses.jsonl",
                "app_data/consultations/transport-2024/outputs/mapping/2024-01-15/mapping.jsonl",
                "app_data/consultations/education-2024/some_file.txt",
                "app_data/other_folder/not_consultation.txt",  # Should be ignored
            ]

            for key in test_objects:
                minio_client.put_object(
                    Bucket=minio_test_bucket,
                    Key=key,
                    Body=b"test content"
                )
                created_keys.append(key)

            # Execute: Call the function under test
            result = get_consultation_folders()

            # Verify: Check correct folders were extracted
            assert set(result) == {"healthcare-2024", "transport-2024", "education-2024"}
            assert len(result) == 3

        finally:
            # Cleanup: Delete all objects we created
            for key in created_keys:
                try:
                    minio_client.delete_object(
                        Bucket=minio_test_bucket,
                        Key=key
                    )
                except Exception as e:
                    logger.warning("Failed to cleanup object {key}: {e}", key=key, e=e)
