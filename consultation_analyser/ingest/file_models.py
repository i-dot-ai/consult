from typing import Any, Literal

from botocore.exceptions import ClientError
from django.conf import settings
from pydantic import BaseModel, computed_field, field_validator

from consultation_analyser.consultations.models import ResponseAnnotation

logger = settings.LOGGER


def read_from_s3(model, client, bucket: str, key: str, raise_error_if_file_missing: bool = True):
    try:
        s3_obj = client.get_object(Bucket=bucket, Key=key)
    except ClientError:
        if raise_error_if_file_missing is False:
            return  # early return as no data found

        logger.error("file not found, bucket={bucket}, key={key}", bucket=bucket, key=key)
        msg = f"file not found {bucket}/{key}"
        raise ValueError(msg)

    for line in s3_obj["Body"].iter_lines():
        yield model.model_validate_json(line.decode("utf-8"))


class DetailDetection(BaseModel):
    themefinder_id: int
    evidence_rich: Literal["YES", "NO"] = "NO"

    @field_validator("evidence_rich", mode="before")
    def coerce_null_evidence_rich(cls, v):
        return "NO" if v is None else v

    @computed_field  # type:ignore
    @property
    def evidence_rich_bool(self) -> bool:
        return self.evidence_rich == "YES"


class SentimentRecord(BaseModel):
    themefinder_id: int
    sentiment: Literal["AGREEMENT", "DISAGREEMENT", "UNCLEAR"] = "UNCLEAR"

    @field_validator("sentiment", mode="before")
    def coerce_null_sentiment(cls, v):
        return "UNCLEAR" if v is None else v

    @computed_field  # type:ignore
    @property
    def sentiment_enum(self) -> Any:
        match self.sentiment:
            case "AGREEMENT":
                return ResponseAnnotation.Sentiment.AGREEMENT  # type:ignore
            case "DISAGREEMENT":
                return ResponseAnnotation.Sentiment.DISAGREEMENT  # type:ignore
            case _:
                return ResponseAnnotation.Sentiment.UNCLEAR  # type:ignore
