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


class Consultation(UUIDPrimaryKeyBase):
    name = models.CharField(max_length=256, blank=False)


class Section(UUIDPrimaryKeyBase):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    text = models.TextField(blank=True)


class Question(UUIDPrimaryKeyBase):
    text = models.CharField(max_length=None)  # no idea what's a sensible value for max_length
    slug = models.CharField(blank=False, null=False, max_length=256)
    has_free_text = models.BooleanField(default=False)
    multiple_choice_options = models.JSONField(default=list)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)


class Respondent(UUIDPrimaryKeyBase):
    # Characteristics may be different for different consultations
    pass


class Theme(UUIDPrimaryKeyBase):
    label = models.CharField(max_length=256, blank=True)
    summary = models.TextField(blank=True)
    keywords = models.JSONField(default=list)


class Answer(UUIDPrimaryKeyBase):
    multiple_choice_responses = models.JSONField(default=list) # Multiple choice can have more than one response
    free_text = models.TextField(blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, blank=True) # For now, just one theme per answer
