from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.urls import reverse

from backend.consultations import models
from backend.consultations.models import Question


def get_sorted_theme_string(themes: list[models.SelectedTheme]) -> str:
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
            kwargs={"consultation_pk": question.consultation.pk},
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


def isoformat(dt: datetime) -> str:
    """
    Convert a datetime to ISO 8601 format with the correct timezone
    and 'Z' used instead of '+00:00' to convery UTC timezone. This is
    used to match the format returned by the API.

    There is no option to output 'Z' directly from datetime.isoformat(),
    so we replace it manually.
    See: https://github.com/python/cpython/issues/90772
    """
    localtime = dt.astimezone(ZoneInfo(settings.TIME_ZONE))
    return localtime.isoformat().replace("+00:00", "Z")
