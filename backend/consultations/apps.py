from django.apps import AppConfig
from django.conf import settings

from consultations.utils import s3


class ConsultationsConfig(AppConfig):
    name = "consultations"
