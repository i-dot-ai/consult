import uuid
from django.db import models


class UUIDPrimaryKeyBase(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class SlugPrimaryKeyBase(models.Model):
    class Meta:
        abstract = True

    slug = models.CharField(primary_key=True, blank=False, max_length=256)


class Consultation(SlugPrimaryKeyBase):
    name = models.CharField(max_length=256, blank=False)


class Section(SlugPrimaryKeyBase):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True)
    text = models.TextField(blank=True)


class Question(SlugPrimaryKeyBase):
    text = models.CharField(max_length=None)  # no idea what's a sensible value for max_length
    has_free_text = models.BooleanField(default=False)
    multiple_choice_options = models.JSONField(default=list)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True)


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
