# Create your models here.
from django.db import models


class Question(models.Model):
    text = models.CharField(max_length=None)  # no idea what's a sensible value for max_length
    slug = models.CharField(max_length=256)
