import csv
from io import TextIOWrapper
from pathlib import Path
from typing import BinaryIO

from django.contrib.postgres.search import SearchVector
from django.db import transaction
from openpyxl import load_workbook

from consultations.models import Consultation, Question, Respondent, Response


def read_consultation_file(
    file: BinaryIO, filename: str, data_source: str | None = None
) -> tuple[list[str], list[list[str | None]]]:
    extension = Path(filename).suffix.lower()
    file.seek(0)

    if extension == ".csv":
        wrapper = TextIOWrapper(file, encoding="utf-8-sig", newline="")
        try:
            rows = list(csv.reader(wrapper))
        finally:
            wrapper.detach()
    else:
        workbook = load_workbook(file, read_only=True, data_only=True)
        try:
            sheet = workbook.active
            if sheet is None:
                raise ValueError("XLSX file has no visible worksheet.")
            rows = [list(row) for row in sheet.iter_rows(values_only=True)]
        finally:
            workbook.close()

    file.seek(0)
    if not rows:
        raise ValueError("File must contain a header row.")

    if data_source == Consultation.DataSource.QUALTRICS:
        question_row = rows[1] if len(rows) > 1 else []
        raw_response_rows = rows[3:]
    else:
        question_row = rows[0]
        raw_response_rows = rows[1:]

    questions = ["" if value is None else str(value) for value in question_row]
    if not questions:
        raise ValueError("File must contain at least one question column.")

    response_rows = [
        [None if value is None or value == "" else str(value) for value in row[: len(questions)]]
        + [None] * max(0, len(questions) - len(row))
        for row in raw_response_rows
    ]
    return questions, response_rows


@transaction.atomic
def import_consultation_data(
    consultation: Consultation, question_texts: list[str], response_rows: list[list[str | None]]
) -> tuple[int, int]:
    next_question_number = (
        consultation.question_set.order_by("-number").values_list("number", flat=True).first() or 0
    )
    questions = Question.objects.bulk_create(
        [
            Question(
                consultation=consultation,
                text=text,
                number=next_question_number + index,
                type=None,
            )
            for index, text in enumerate(question_texts, start=1)
        ]
    )
    respondents = Respondent.objects.bulk_create(
        [
            Respondent(consultation=consultation, themefinder_id=index)
            for index, _ in enumerate(response_rows, start=1)
        ]
    )
    # free_text is dual-written with text so the pipeline and model consumers
    # that read the legacy column (response counts, search vectors, sample
    # answers) work for V2 consultations without further changes.
    responses = Response.objects.bulk_create(
        [
            Response(
                question=question,
                respondent=respondent,
                text=text,
                free_text=text,
            )
            for respondent, row in zip(respondents, response_rows, strict=True)
            for question, text in zip(questions, row, strict=True)
        ],
        batch_size=1000,
    )

    # The post_save signal behind search_vector does not fire for bulk_create,
    # so build the vectors directly (equivalent to the per-row save the V1
    # importer relied on). free_text is populated exactly where text is.
    Response.objects.filter(question__consultation=consultation, free_text__isnull=False).update(
        search_vector=SearchVector("free_text", config="english")
    )

    # Populate the denormalised counts the UI reads; nothing else calculates
    # them after a V2 import.
    for question in questions:
        question.update_response_counts()

    return len(questions), len(responses)
