from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from consultations.models import Consultation, FileUpload, Question, Respondent, Response
from ingest.jobs import add_consultation_job


@pytest.mark.django_db
def test_add_consultation_job_imports_raw_file(consultation, non_staff_user):
    s3_key = default_storage.save(
        f"consultations/uploads/{consultation.id}/responses.csv",
        ContentFile(b"Name,Feedback\nAlice,Very useful\nBob,"),
    )
    file_upload = FileUpload.objects.create(
        consultation=consultation,
        uploaded_by=non_staff_user,
        s3_key=s3_key,
    )

    add_consultation_job(file_upload.id)

    file_upload.refresh_from_db()
    consultation.refresh_from_db()
    assert file_upload.status == FileUpload.Status.COMPLETED
    assert file_upload.error_message == ""
    assert consultation.servey_import_status == Consultation.ServeyImportStatus.PENDING_QUESTIONS
    questions = list(Question.objects.filter(consultation=consultation).order_by("number"))
    assert [question.text for question in questions] == ["Name", "Feedback"]
    assert [question.type for question in questions] == [None, None]
    respondents = list(
        Respondent.objects.filter(consultation=consultation).order_by("themefinder_id")
    )
    assert [respondent.themefinder_id for respondent in respondents] == [1, 2]
    assert Response.objects.filter(question__consultation=consultation).count() == 4
    assert Response.objects.get(question=questions[1], respondent=respondents[1]).text is None


@pytest.mark.django_db
def test_add_consultation_job_records_failure(consultation, non_staff_user):
    file_upload = FileUpload.objects.create(
        consultation=consultation,
        uploaded_by=non_staff_user,
        s3_key="consultations/uploads/missing.csv",
    )

    with (
        patch("ingest.jobs.logger.exception") as log_exception,
        pytest.raises(FileNotFoundError),
    ):
        add_consultation_job(file_upload.id)

    file_upload.refresh_from_db()
    consultation.refresh_from_db()
    assert file_upload.status == FileUpload.Status.FAILED
    assert file_upload.error_message
    assert consultation.servey_import_status == Consultation.ServeyImportStatus.IMPORT_FAILED
    log_exception.assert_called_once()
