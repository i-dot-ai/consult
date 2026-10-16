from io import BytesIO
from zipfile import ZipFile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from consultations.models import Consultation, FileUpload


def xlsx_file(rows, filename="responses.xlsx"):
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    content = BytesIO()
    workbook.save(content)
    return SimpleUploadedFile(filename, content.getvalue())


def xlsx_file_with_control_character():
    original = xlsx_file([["Question"], ["Invalid answer"]])
    content = BytesIO()
    with ZipFile(original) as source, ZipFile(content, "w") as destination:
        for entry in source.infolist():
            entry_content = source.read(entry.filename)
            if entry.filename == "xl/worksheets/sheet1.xml":
                entry_content = entry_content.replace(b"Invalid answer", b"Invalid\x01answer")
            destination.writestr(entry, entry_content)
    return SimpleUploadedFile("responses.xlsx", content.getvalue())


def validate(client, consultation, token, uploaded_file):
    return client.post(
        reverse("consultation-v2-deep-validation", kwargs={"pk": consultation.id}),
        data={"file": uploaded_file},
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.mark.django_db
def test_citizen_space_csv_passes_deep_validation(client, consultation, non_staff_user_token):
    consultation.data_source = Consultation.DataSource.CITIZEN_SPACE
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        SimpleUploadedFile("responses.csv", b"Question one,Question two\nAnswer one,Answer two"),
    )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "rejection_type": None,
        "message": "File passed deep validation.",
        "errors": [],
        "question_count": 2,
        "response_count": 2,
        "blank_cell_count": 0,
    }
    assert not FileUpload.objects.exists()


@pytest.mark.django_db
def test_csv_with_quoted_commas_passes_deep_validation(client, consultation, non_staff_user_token):
    consultation.data_source = Consultation.DataSource.CITIZEN_SPACE
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        SimpleUploadedFile("responses.csv", b'Question one,Question two\n"London, UK",Answer two'),
    )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "rejection_type": None,
        "message": "File passed deep validation.",
        "errors": [],
        "question_count": 2,
        "response_count": 2,
        "blank_cell_count": 0,
    }


@pytest.mark.django_db
def test_csv_with_inconsistent_column_counts_is_rejected(
    client, consultation, non_staff_user_token
):
    consultation.data_source = Consultation.DataSource.CITIZEN_SPACE
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        SimpleUploadedFile("responses.csv", b"Question one,Question two\nAnswer one"),
    )

    assert response.status_code == 200
    assert response.json()["rejection_type"] == "hard"
    assert response.json()["errors"][0]["code"] == "invalid_file_type"


@pytest.mark.django_db
def test_qualtrics_xlsx_uses_second_row_for_questions_and_rows_four_onwards_for_responses(
    client, consultation, non_staff_user_token
):
    consultation.data_source = Consultation.DataSource.QUALTRICS
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        xlsx_file(
            [
                ["Qualtrics metadata"],
                ["Question one", "Question two"],
                ["Import IDs"],
                ["Answer one", "Answer two"],
                ["Answer three", "Answer four"],
            ]
        ),
    )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "rejection_type": None,
        "message": "File passed deep validation.",
        "errors": [],
        "question_count": 2,
        "response_count": 4,
        "blank_cell_count": 0,
    }


@pytest.mark.django_db
def test_successful_validation_counts_blank_cells(client, consultation, non_staff_user_token):
    consultation.data_source = Consultation.DataSource.QUALTRICS
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        xlsx_file(
            [
                ["Ignored", "Ignored", "Ignored"],
                ["Question one", "Question two", "Question three"],
                ["Ignored", "Ignored", "Ignored"],
                ["Answer one", None, "Answer three"],
                [None, "Answer five", "Answer six"],
            ]
        ),
    )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "rejection_type": None,
        "message": "File passed deep validation.",
        "errors": [],
        "question_count": 3,
        "response_count": 4,
        "blank_cell_count": 2,
    }


@pytest.mark.django_db
def test_formula_cells_are_collected_as_soft_rejections(client, consultation, non_staff_user_token):
    consultation.data_source = Consultation.DataSource.QUALTRICS
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        xlsx_file(
            [
                ["Ignored"],
                ["=1+1", "Question two"],
                ["Ignored"],
                ["=2+2", "Answer two"],
            ]
        ),
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["rejection_type"] == "soft"
    assert response.json()["errors"] == [
        {
            "code": "formula",
            "message": "Formulas are not allowed in question or response cells.",
            "cell": "A2",
        },
        {
            "code": "formula",
            "message": "Formulas are not allowed in question or response cells.",
            "cell": "A4",
        },
    ]
    assert response.json()["question_count"] == 2
    assert response.json()["response_count"] == 2
    assert response.json()["blank_cell_count"] == 0


@pytest.mark.django_db
def test_control_character_is_an_immediate_hard_rejection(
    client, consultation, non_staff_user_token
):
    consultation.data_source = Consultation.DataSource.CITIZEN_SPACE
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        SimpleUploadedFile("responses.csv", b"Question\nInvalid\x01answer"),
    )

    assert response.status_code == 200
    assert response.json()["rejection_type"] == "hard"
    assert response.json()["errors"] == [
        {
            "code": "illegal_control_character",
            "message": "The cell contains an unreadable character.",
            "cell": "A2",
        }
    ]


@pytest.mark.django_db
def test_xlsx_control_character_reports_the_cell(client, consultation, non_staff_user_token):
    consultation.data_source = Consultation.DataSource.CITIZEN_SPACE
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        xlsx_file_with_control_character(),
    )

    assert response.status_code == 200
    assert response.json()["rejection_type"] == "hard"
    assert response.json()["errors"][0]["code"] == "illegal_control_character"
    assert response.json()["errors"][0]["cell"] == "A2"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("content", "expected_code"),
    [
        (b"", "empty_questions"),
        (b"Question\n", "empty_responses"),
        (b"\nAnswer", "empty_questions"),
    ],
)
def test_empty_question_or_response_row_is_a_hard_rejection(
    client, consultation, non_staff_user_token, content, expected_code
):
    consultation.data_source = Consultation.DataSource.CITIZEN_SPACE
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        SimpleUploadedFile("responses.csv", content),
    )

    assert response.status_code == 200
    assert response.json()["rejection_type"] == "hard"
    assert response.json()["errors"][0]["code"] == expected_code


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("responses.xlsx", b"Question\nAnswer"),
        ("responses.csv", xlsx_file([["Question"], ["Answer"]]).read()),
        ("responses.csv", b"%PDF-1.7\nQuestion\nAnswer"),
        ("responses.txt", b"Question\nAnswer"),
    ],
)
def test_file_type_requires_matching_extension_and_signature(
    client, consultation, non_staff_user_token, filename, content
):
    consultation.data_source = Consultation.DataSource.CITIZEN_SPACE
    consultation.save(update_fields=["data_source"])

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        SimpleUploadedFile(filename, content),
    )

    assert response.status_code == 200
    assert response.json()["rejection_type"] == "hard"
    assert response.json()["errors"][0]["code"] == "invalid_file_type"


@pytest.mark.django_db
def test_missing_data_source_is_a_hard_rejection(client, consultation, non_staff_user_token):
    response = validate(
        client,
        consultation,
        non_staff_user_token,
        SimpleUploadedFile("responses.csv", b"Question\nAnswer"),
    )

    assert response.status_code == 200
    assert response.json()["rejection_type"] == "hard"
    assert response.json()["errors"][0]["code"] == "unsupported_data_source"


@pytest.mark.django_db
def test_deep_validation_rejects_unassigned_user(client, consultation, non_staff_user_token):
    consultation.users.clear()

    response = validate(
        client,
        consultation,
        non_staff_user_token,
        SimpleUploadedFile("responses.csv", b"Question\nAnswer"),
    )

    assert response.status_code == 403
