from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from consultations.api_v2.serializers import ConsultationFileUploadSerializerV2
from consultations.models import Consultation, FileUpload, Question, Respondent


def xlsx_file(rows, filename="responses.xlsx"):
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    content = BytesIO()
    workbook.save(content)
    return SimpleUploadedFile(filename, content.getvalue())


@pytest.mark.django_db
def test_v2_upload_consultation_file(client, consultation, non_staff_user_token):
    url = reverse("consultation-v2-upload", kwargs={"pk": consultation.id})
    uploaded_file = SimpleUploadedFile(
        "responses.csv",
        b"What is your name?,What do you think?\nAlice,Very useful\nBob,Needs work",
    )

    with patch("consultations.api_v2.views.consultation.add_consultation_job.delay") as delay:
        response = client.post(
            url,
            data={"file": uploaded_file},
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 202
    file_upload = FileUpload.objects.get(id=response.json()["id"])
    assert file_upload.consultation == consultation
    assert file_upload.uploaded_by_id is not None
    assert file_upload.s3_key == f"consultations/uploads/{consultation.id}/{file_upload.id}.csv"
    assert response.json()["s3_key"] == file_upload.s3_key
    assert response.json()["status"] == FileUpload.Status.PENDING
    assert response.json()["servey_import_status"] == Consultation.ServeyImportStatus.FILE_UPLOADING
    delay.assert_called_once_with(file_upload.id)
    consultation.refresh_from_db()
    assert consultation.servey_import_status == Consultation.ServeyImportStatus.FILE_UPLOADING
    assert not Question.objects.filter(consultation=consultation).exists()
    assert not Respondent.objects.filter(consultation=consultation).exists()


@pytest.mark.django_db
def test_v2_upload_accepts_xlsx_case_insensitively(client, consultation, non_staff_user_token):
    with patch("consultations.api_v2.views.consultation.add_consultation_job.delay"):
        response = client.post(
            reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
            data={"file": xlsx_file([["Question"], ["Answer"]], "responses.XLSX")},
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 202
    assert response.json()["s3_key"].endswith(".xlsx")
    assert not Question.objects.filter(consultation=consultation).exists()


@pytest.mark.django_db
def test_v2_upload_rejects_invalid_xlsx_without_persisting_data(
    client, consultation, non_staff_user_token
):
    response = client.post(
        reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
        data={"file": SimpleUploadedFile("responses.xlsx", b"not a workbook")},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert not FileUpload.objects.exists()
    assert not Question.objects.filter(consultation=consultation).exists()
    assert not Respondent.objects.filter(consultation=consultation).exists()


@pytest.mark.django_db
def test_v2_upload_rejects_xlsx_without_visible_worksheet(
    client, consultation, non_staff_user_token
):
    workbook = MagicMock(active=None)
    with (
        patch("ingest.consultation_file.load_workbook", return_value=workbook),
        patch("consultations.api_v2.views.consultation.logger.exception") as log_exception,
    ):
        response = client.post(
            reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
            data={"file": SimpleUploadedFile("responses.xlsx", b"workbook")},
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    assert response.json()["file"] == "XLSX file has no visible worksheet."
    workbook.close.assert_called_once_with()
    log_exception.assert_called_once_with(
        "Error uploading file {file_name}",
        file_name="responses.xlsx",
    )
    assert not FileUpload.objects.exists()


@pytest.mark.django_db
def test_v2_upload_rejects_second_file(client, consultation, non_staff_user_token):
    FileUpload.objects.create(
        consultation=consultation,
        uploaded_by=consultation.created_by,
        s3_key="consultations/uploads/existing.csv",
    )

    with patch("consultations.api_v2.views.consultation.add_consultation_job.delay") as delay:
        response = client.post(
            reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
            data={"file": SimpleUploadedFile("responses.csv", b"Question\nAnswer")},
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    assert response.json()["file"] == "A file has already been uploaded for this consultation."
    assert FileUpload.objects.filter(consultation=consultation).count() == 1
    delay.assert_not_called()


@pytest.mark.django_db
def test_v2_upload_records_queue_failure(client, consultation, non_staff_user_token):
    with (
        patch(
            "consultations.api_v2.views.consultation.add_consultation_job.delay",
            side_effect=RuntimeError("Queue unavailable"),
        ),
        pytest.raises(RuntimeError, match="Queue unavailable"),
    ):
        client.post(
            reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
            data={"file": SimpleUploadedFile("responses.csv", b"Question\nAnswer")},
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    file_upload = FileUpload.objects.get(consultation=consultation)
    assert file_upload.status == FileUpload.Status.FAILED
    assert file_upload.error_message == "Queue unavailable"
    consultation.refresh_from_db()
    assert consultation.servey_import_status == Consultation.ServeyImportStatus.IMPORT_FAILED


@pytest.mark.django_db
def test_v2_upload_rejects_unsupported_file_type(client, consultation, non_staff_user_token):
    response = client.post(
        reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
        data={"file": SimpleUploadedFile("responses.txt", b"not supported")},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert response.json()["file"] == ["File must be a CSV or XLSX file."]
    assert not FileUpload.objects.exists()


@pytest.mark.django_db
def test_v2_upload_rejects_file_over_size_limit(client, consultation, non_staff_user_token):
    uploaded_file = SimpleUploadedFile("responses.csv", b"content")

    with patch.object(
        ConsultationFileUploadSerializerV2,
        "MAX_FILE_SIZE",
        uploaded_file.size - 1,
    ):
        response = client.post(
            reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
            data={"file": uploaded_file},
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    assert response.json()["file"] == ["File must not exceed 200 MiB."]
    assert not FileUpload.objects.exists()


@pytest.mark.django_db
def test_v2_upload_rejects_unassigned_user(client, consultation, non_staff_user_token):
    consultation.users.clear()

    response = client.post(
        reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
        data={"file": SimpleUploadedFile("responses.csv", b"content")},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 403
    assert not FileUpload.objects.exists()
