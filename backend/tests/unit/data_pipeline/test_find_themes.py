from pathlib import Path
from unittest.mock import Mock, patch

from data_pipeline.find_themes import upload_find_themes_outputs


@patch("data_pipeline.find_themes.boto3")
@patch("data_pipeline.find_themes.settings")
def test_upload_find_themes_outputs_preserves_s3_contract(settings, boto3, tmp_path: Path):
    settings.AWS_BUCKET_NAME = "bucket"
    settings.AWS_ACCOUNT_ID = "123456789012"
    output = tmp_path / "outputs"
    question = output / "question_part_1"
    question.mkdir(parents=True)
    (question / "clustered_themes.json").write_text('{"theme_nodes": []}')
    client = Mock()
    boto3.client.return_value = client

    upload_find_themes_outputs("consultation-code", "2026-11-23", output)

    call = client.put_object.call_args.kwargs
    assert call["Bucket"] == "bucket"
    assert call["Key"] == (
        "app_data/consultations/consultation-code/outputs/sign_off/"
        "2026-11-23/question_part_1/clustered_themes.json"
    )
    assert call["ExpectedBucketOwner"] == "123456789012"
