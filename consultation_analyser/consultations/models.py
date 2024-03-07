import uuid
from django.db import models


class UUIDPrimaryKeyBase(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    modified_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        abstract = True
        ordering = ["created_at"]


class Consultation(UUIDPrimaryKeyBase, TimeStampedModel):
    name = models.CharField(max_length=256, blank=False)
    slug = models.CharField(blank=False, null=False, max_length=256)


class Section(UUIDPrimaryKeyBase, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True)
    text = models.TextField(blank=True)
    slug = models.CharField(blank=False, null=False, max_length=256)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["slug", "consultation"], name="unique_section_consultation"),
        ]


class Question(UUIDPrimaryKeyBase, TimeStampedModel):
    text = models.CharField(max_length=None)  # no idea what's a sensible value for max_length
    slug = models.CharField(blank=False, null=False, max_length=256)
    has_free_text = models.BooleanField(default=False)
    multiple_choice_options = models.JSONField(default=list, null=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["slug", "section"], name="unique_question_section"),
        ]


class ConsultationResponse(UUIDPrimaryKeyBase, TimeStampedModel):
    # Characteristics may be different for different consultations
    pass


class Theme(UUIDPrimaryKeyBase, TimeStampedModel):
    label = models.CharField(max_length=256, blank=True)
    summary = models.TextField(blank=True)
    keywords = models.JSONField(default=list)


class Answer(UUIDPrimaryKeyBase, TimeStampedModel):
    multiple_choice_responses = models.JSONField(default=list, null=True) # Multiple choice can have more than one response
    free_text = models.TextField(blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    consultation_response = models.ForeignKey(ConsultationResponse, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, blank=True, null=True) # For now, just one theme per answer
