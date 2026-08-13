from django.apps import AppConfig
from django.conf import settings

from consultations.utils import s3


class ConsultationsConfig(AppConfig):
    name = "consultations"

    def ready(self):
        logger = settings.LOGGER
        if settings.ENVIRONMENT.upper() in ["LOCAL", "TEST"]:
            s3_client = s3.get_s3_client()
            buckets = s3_client.list_buckets()["Buckets"]
            if not any(bucket["Name"] == settings.AWS_BUCKET_NAME for bucket in buckets):
                logger.info(
                    "Bucket not found, creating - {bucket_name}",
                    bucket_name=settings.AWS_BUCKET_NAME,
                )
                s3_client.create_bucket(Bucket=settings.AWS_BUCKET_NAME)
