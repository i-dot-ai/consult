"""One Response row per respondent per selected option, text = the option. Every
reader of multiple-choice data goes through here so the legacy MultiChoiceAnswer
and chosen_options path can be removed in one place. Nothing here checks
DATA_SETUP_V2_ENABLED; callers gate on Question.answers_from_responses.
"""

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from django.db.models import Count, Q, QuerySet

from consultations.models import Question, Response


def answer_rows(question: Question, respondent_ids: Iterable[UUID] | None = None) -> QuerySet:
    answers_question = question.answers_question
    if answers_question is None:
        return Response.objects.none()
    rows = Response.objects.filter(question=answers_question).exclude(
        Q(text__isnull=True) | Q(text="")
    )
    if respondent_ids is not None:
        rows = rows.filter(respondent_id__in=respondent_ids)
    return rows


def count_option_responses(
    question: Question, respondent_ids: Iterable[UUID] | None = None
) -> list[dict]:
    """Each distinct answer with how many respondents selected it, most selected first."""
    return [
        {"text": row["text"], "response_count": row["response_count"]}
        for row in answer_rows(question, respondent_ids)
        .values("text")
        .annotate(response_count=Count("respondent_id", distinct=True))
        .order_by("-response_count", "text")
    ]


def count_answering_respondents(
    question: Question, respondent_ids: Iterable[UUID] | None = None
) -> int:
    return answer_rows(question, respondent_ids).values("respondent_id").distinct().count()


def list_selected_texts(
    question: Question, respondent_ids: Iterable[UUID]
) -> dict[UUID, list[str]]:
    """Selected answers per respondent; respondents who selected nothing are absent."""
    selected: dict[UUID, list[str]] = defaultdict(list)
    for respondent_id, text in (
        answer_rows(question, respondent_ids)
        .order_by("respondent_id", "text")
        .values_list("respondent_id", "text")
    ):
        selected[respondent_id].append(text)
    return dict(selected)
