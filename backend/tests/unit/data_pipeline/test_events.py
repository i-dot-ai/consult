import json
from unittest.mock import Mock, patch

from data_pipeline.events import publish_find_themes_event


@patch("data_pipeline.events.boto3")
@patch("data_pipeline.events.settings")
def test_publish_find_themes_event_uses_worker_event_contract(settings, boto3):
    settings.ENVIRONMENT = "DEPLOYED"
    client = Mock()
    boto3.client.return_value = client

    publish_find_themes_event(
        status="SUCCEEDED",
        consultation_code="consultation-code",
        consultation_name="Consultation",
        user_id=123,
        job_id="rq-job-id",
        context_id="context-id",
    )

    entry = client.put_events.call_args.kwargs["Entries"][0]
    assert entry["Source"] == "consult.worker"
    assert entry["DetailType"] == "Find Themes Job State Change"
    assert json.loads(entry["Detail"])["status"] == "SUCCEEDED"


@patch("data_pipeline.events.boto3")
@patch("data_pipeline.events.settings")
def test_publish_find_themes_event_is_disabled_locally(settings, boto3):
    settings.ENVIRONMENT = "LOCAL"

    publish_find_themes_event(
        status="RUNNING",
        consultation_code="consultation-code",
        consultation_name="Consultation",
        user_id=123,
        job_id=None,
        context_id="context-id",
    )

    boto3.client.assert_not_called()


@patch("data_pipeline.events.logger")
@patch("data_pipeline.events.boto3")
@patch("data_pipeline.events.settings")
def test_publish_find_themes_event_logs_partial_failure(settings, boto3, logger):
    settings.ENVIRONMENT = "DEPLOYED"
    boto3.client.return_value.put_events.return_value = {
        "FailedEntryCount": 1,
        "Entries": [{"ErrorCode": "InternalFailure"}],
    }

    publish_find_themes_event(
        status="FAILED",
        consultation_code="consultation-code",
        consultation_name="Consultation",
        user_id=123,
        job_id="rq-job-id",
        context_id="context-id",
    )

    logger.error.assert_called_once()
