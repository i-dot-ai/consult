from django_rq import job
from django.core.files.storage import default_storage as storage

from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.authentication.models import User


@job("default")
def async_upload_consultation(file_path, user_id):
    user = User.objects.get(id=user_id)
    saved_file = storage.open(file_path, "r")

    upload_consultation(saved_file, user)
