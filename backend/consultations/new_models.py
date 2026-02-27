from django.db import models

from authentication.models import User
from consultations.models import UUIDPrimaryKeyModel, TimeStampedModel, Consultation


class FileUpload(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, editable=False)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    s3_key = models.TextField(null=True, blank=True)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        indexes = [
            models.Index(fields=["consultation", "themefinder_id"]),
        ]
