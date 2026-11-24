"""One Response row per respondent per selected option, text = the option. Every
reader of multiple-choice data goes through here so the legacy MultiChoiceAnswer
and chosen_options path can be removed in one place. Nothing here checks
DATA_SETUP_V2_ENABLED; callers gate on Question.answers_from_responses.
"""

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from django.db.models import Count, Exists, OuterRef, Q, QuerySet

from consultations.models import Question, Response


def count_option_responses(
    question: Question, respondent_ids: Iterable[UUID] | None = None
) -> list[dict]:
    """Each distinct answer with how many respondents selected it, most selected first.
    Limiting to respondents keeps every answer listed and only changes the counts."""
    counts = {
        row["text"]: row["response_count"]
        for row in question.answer_rows(respondent_ids)
        .values("text")
        .annotate(response_count=Count("respondent_id", distinct=True))
    }
    texts = (
        counts
        if respondent_ids is None
        else question.answer_rows().values_list("text", flat=True).distinct()
    )
    return sorted(
        ({"text": text, "response_count": counts.get(text, 0)} for text in texts),
        key=lambda item: (-item["response_count"], item["text"]),
    )


def attach_option_counts(questions: Iterable[Question]) -> None:
    """Set `prefetched_option_counts` on each question from a single grouped query."""
    questions = list(questions)
    answers_question_ids = {
        question.answers_question_id
        for question in questions
        if question.answers_from_responses and question.answers_question_id
    }
    counts: dict[UUID, list[dict]] = defaultdict(list)
    rows = (
        Response.objects.filter(question_id__in=answers_question_ids)
        .exclude(Q(text__isnull=True) | Q(text=""))
        .values("question_id", "text")
        .annotate(response_count=Count("respondent_id", distinct=True))
        .order_by("question_id", "-response_count", "text")
    )
    for row in rows:
        counts[row["question_id"]].append(
            {"text": row["text"], "response_count": row["response_count"]}
        )
    for question in questions:
        if question.answers_from_responses:
            answers_question_id = question.answers_question_id
            question.prefetched_option_counts = (
                counts.get(answers_question_id, []) if answers_question_id else []
            )


def count_answering_respondents(
    question: Question, respondent_ids: Iterable[UUID] | None = None
) -> int:
    return question.answer_rows(respondent_ids).values("respondent_id").distinct().count()


def list_selected_texts(
    question: Question, respondent_ids: Iterable[UUID]
) -> dict[UUID, list[str]]:
    """Selected answers per respondent; respondents who selected nothing are absent."""
    selected: dict[UUID, list[str]] = defaultdict(list)
    for respondent_id, text in (
        question.answer_rows(respondent_ids)
        .order_by("respondent_id", "text")
        .values_list("respondent_id", "text")
    ):
        selected[respondent_id].append(text)
    return dict(selected)


def closed_answer_rows(consultation_id: UUID) -> QuerySet:
    return (
        Response.objects.filter(
            question__consultation_id=consultation_id,
            question__type__in=[Question.QuestionType.CLOSED, Question.QuestionType.DEMOGRAPHIC],
        )
        .exclude(Q(text__isnull=True) | Q(text=""))
        .select_related("question")
        .order_by("text")
    )


def filter_responses_by_answers(queryset: QuerySet, texts: Iterable[str]) -> QuerySet:
    """Responses whose respondent selected any of the texts on the response's own
    question or, for a hybrid, on its closed sibling."""
    selected = Response.objects.filter(
        respondent_id=OuterRef("respondent_id"), text__in=list(texts)
    ).filter(
        Q(question_id=OuterRef("question_id"))
        | Q(question_id=OuterRef("question__closed_question_id"))
    )
    return queryset.filter(Exists(selected))
