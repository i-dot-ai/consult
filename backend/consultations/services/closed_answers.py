"""One Response row per respondent per selected option, text = the option."""

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from django.db.models import Count, Exists, OuterRef, Q, QuerySet

from consultations.models import Consultation, Question, Response


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
    # Under a filter a second query lists every answer, so the ones the filtered
    # respondents did not pick stay in the result with a zero count
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
        question.answers_question_id for question in questions if question.answers_question_id
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
        # The v2 response serializer reads question.type and question.text off this prefetch
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


def demographic_answer_id(question_id: UUID, text: str) -> str:
    return f"{question_id}:{text}"


def split_demographic_answer_id(value: str) -> tuple[UUID, str] | None:
    """Inverse of demographic_answer_id; None for anything else, such as a legacy option id."""
    question_part, separator, text = value.partition(":")
    if not separator:
        return None
    try:
        return UUID(question_part), text
    except ValueError:
        return None


def filter_responses_by_demographic_answers(
    queryset: QuerySet, selections: dict[UUID, Iterable[str]]
) -> QuerySet:
    """OR within a demographic question, AND across questions."""
    for question_id, texts in selections.items():
        queryset = queryset.filter(
            Exists(
                Response.objects.filter(
                    respondent_id=OuterRef("respondent_id"),
                    question_id=question_id,
                    text__in=list(texts),
                )
            )
        )
    return queryset


def count_demographic_answers(
    consultation: Consultation, respondent_ids: Iterable[UUID] | None = None
) -> list[dict]:
    """Every demographic answer in the consultation with its respondent count, in the
    shape the v1 demographics endpoint serialises. Limiting to respondents keeps every
    answer listed and only changes the counts."""
    rows = Response.objects.filter(
        question__consultation=consultation,
        question__type=Question.QuestionType.DEMOGRAPHIC,
    ).exclude(Q(text__isnull=True) | Q(text=""))
    answers = (
        rows.values("question_id", "question__text", "question__number", "text")
        .distinct()
        .order_by("question__number", "text")
    )
    counted = rows
    if respondent_ids is not None:
        counted = counted.filter(respondent_id__in=respondent_ids)
    counts = {
        (row["question_id"], row["text"]): row["count"]
        for row in counted.values("question_id", "text").annotate(
            count=Count("respondent_id", distinct=True)
        )
    }
    return [
        {
            "id": demographic_answer_id(answer["question_id"], answer["text"]),
            "field_name": answer["question__text"],
            "field_value": answer["text"],
            "count": counts.get((answer["question_id"], answer["text"]), 0),
        }
        for answer in answers
    ]


def has_demographic_questions(consultation: Consultation) -> bool:
    return consultation.question_set.filter(type=Question.QuestionType.DEMOGRAPHIC).exists()
