import json
from typing import Literal

import boto3
from django.conf import settings

logger = settings.LOGGER


def publish_find_themes_event(
    *,
    status: Literal["RUNNING", "SUCCEEDED", "FAILED"],
    consultation_code: str,
    consultation_name: str,
    user_id: int,
    job_id: str | None,
    context_id: str,
) -> None:
    """Publish worker lifecycle events consumed by the existing Slack notifier Lambda."""
    if settings.ENVIRONMENT.upper() in {"LOCAL", "TEST"}:
        return
    detail = {
        "job_type": "FIND_THEMES",
        "status": status,
        "consultation_code": consultation_code,
        "consultation_name": consultation_name,
        "user_id": str(user_id),
        "job_id": job_id,
        "context_id": context_id,
    }
    try:
        response = boto3.client("events").put_events(
            Entries=[
                {
                    "Source": "consult.worker",
                    "DetailType": "Find Themes Job State Change",
                    "Detail": json.dumps(detail),
                }
            ]
        )
        if response.get("FailedEntryCount", 0):
            logger.error(
                "EventBridge rejected find-themes lifecycle event for {consultation_code}: "
                "{entries}",
                consultation_code=consultation_code,
                entries=response.get("Entries", []),
            )
    except Exception:
        # Notifications must never change the outcome of the consultation job.
        logger.exception(
            "Failed to publish {status} find-themes event for {consultation_code}",
            status=status,
            consultation_code=consultation_code,
        )
