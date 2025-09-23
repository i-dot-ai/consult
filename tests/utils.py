from django.urls import reverse

from consultation_analyser.consultations import models
from consultation_analyser.consultations.models import Question


def get_sorted_theme_string(themes: list[models.Theme]) -> str:
    return ", ".join(sorted([theme.key if theme.key else theme.name for theme in themes]))


def build_url(url_pattern: str, question: Question) -> str:
    if url_pattern.startswith("consultations-"):
        return reverse(url_pattern, kwargs={"pk": question.consultation.pk})

    if url_pattern.startswith("question-"):
        return reverse(
            url_pattern,
            kwargs={
                "consultation_pk": question.consultation.pk,
                "pk": question.pk,
            },
        )

    if url_pattern.startswith("response-"):
        return reverse(
            url_pattern,
            kwargs={
                "consultation_pk": question.consultation.pk,
                "question_pk": question.pk,
            },
        )

    if url_pattern.startswith("respondent-"):
        return reverse(
            url_pattern,
            kwargs={
                "consultation_pk": question.consultation.pk,
                "pk": question.pk,
            },
        )

    raise ValueError("unrecognised url_pattern")
