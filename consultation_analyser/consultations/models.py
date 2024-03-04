from django.db import models


class Consultation(models.Model):
    class Organisation(models.TextChoices):
        DFE = "dept-for-education", "Department for Education"
        CO = "cabinet-office", "Cabinet Office"

    identifier = models.CharField(max_length=256, blank=False)
    name = models.CharField(max_length=256, blank=False)
    organisation_identifier = models.CharField(max_length=256, choices=Organisation.choices, blank=True)


class Question(models.Model):
    text = models.CharField(max_length=None)  # no idea what's a sensible value for max_length
    slug = models.CharField(max_length=256)
    is_closed = models.BooleanField(default=False)
    is_open = models.BooleanField(default=False)
    closed_response_options = models.JSONField(default=list)
    order = models.IntegerField(blank=True, null=True)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True)


class Respondent(models.Model):
    # These characteristics might be different for different consultations
    age_group = models.CharField(max_length=256, blank=True)
    location = models.CharField(max_length=256, blank=True)
    # TODO - what is capacity?


class Theme(models.Model):
    label = models.CharField(max_length=256, blank=True)
    summary = models.TextField(blank=True)
    keywords = models.JSONField(default=list)


class Answer(models.Model):
    closed_response = models.CharField(max_length=256, blank=True)
    free_text_response = models.TextField(blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, blank=True)
