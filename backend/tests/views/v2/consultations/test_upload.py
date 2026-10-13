from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from consultations.api_v2.serializers import ConsultationFileUploadSerializerV2
from consultations.models import FileUpload, Question, Respondent, Response


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

    response = client.post(
        url,
        data={"file": uploaded_file},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 201
    assert response.json()["question_count"] == 2
    assert response.json()["response_count"] == 4
    file_upload = FileUpload.objects.get(id=response.json()["id"])
    assert file_upload.consultation == consultation
    assert file_upload.uploaded_by_id is not None
    assert file_upload.s3_key == f"consultations/uploads/{consultation.id}/{file_upload.id}.csv"
    assert response.json()["s3_key"] == file_upload.s3_key

    questions = list(Question.objects.filter(consultation=consultation).order_by("number"))
    assert [question.text for question in questions] == [
        "What is your name?",
        "What do you think?",
    ]
    assert [question.type for question in questions] == [None, None]
    assert Respondent.objects.filter(consultation=consultation).count() == 2
    assert list(
        Response.objects.filter(question=questions[1])
        .order_by("respondent__created_at")
        .values_list("text", flat=True)
    ) == ["Very useful", "Needs work"]


@pytest.mark.django_db
def test_v2_upload_accepts_xlsx_case_insensitively(client, consultation, non_staff_user_token):
    response = client.post(
        reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
        data={"file": xlsx_file([["Question"], ["Answer"]], "responses.XLSX")},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 201
    assert response.json()["s3_key"].endswith(".xlsx")
    question = Question.objects.get(consultation=consultation)
    assert question.text == "Question"
    assert question.type is None
    assert Response.objects.get(question=question).text == "Answer"


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
        patch("consultations.api_v2.views.consultation.logger.warning") as log_warning,
    ):
        response = client.post(
            reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
            data={"file": SimpleUploadedFile("responses.xlsx", b"workbook")},
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    assert response.json()["file"] == "XLSX file has no visible worksheet."
    workbook.close.assert_called_once_with()
    log_warning.assert_called_once_with(
        "Error uploading file {file_name}",
        file_name="responses.xlsx",
    )
    assert not FileUpload.objects.exists()


@pytest.mark.django_db
def test_v2_upload_retains_file_when_import_fails(client, consultation, non_staff_user_token):
    import_error = RuntimeError("Import failed")
    with (
        patch(
            "consultations.api_v2.views.consultation.import_consultation_data",
            side_effect=import_error,
        ),
        patch(
            "consultations.api_v2.views.consultation.default_storage.delete",
        ) as delete,
        pytest.raises(RuntimeError, match="Import failed") as raised,
    ):
        client.post(
            reverse("consultation-v2-upload", kwargs={"pk": consultation.id}),
            data={"file": SimpleUploadedFile("responses.csv", b"Question\nAnswer")},
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert raised.value is import_error
    delete.assert_not_called()
    file_upload = FileUpload.objects.get(consultation=consultation)
    assert file_upload.uploaded_by_id is not None
    assert file_upload.s3_key.endswith(".csv")
    assert not Question.objects.filter(consultation=consultation).exists()
    assert not Respondent.objects.filter(consultation=consultation).exists()


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
