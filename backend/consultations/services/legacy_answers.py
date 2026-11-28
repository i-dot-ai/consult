"""Reconcile legacy multiple-choice links against the Response rows that replace them.

Reads the MultiChoiceAnswer and chosen_options tables, so this module goes when they do.
"""

from django.db.models import Case, Exists, F, OuterRef, When

from consultations.models import Consultation, Question, Response


def count_unmatched_legacy_answers(consultation: Consultation) -> int:
    """Selected options with no Response row on the question that should hold them.

    The target is the question itself when it is closed and its closed sibling when it
    is open, the same mapping the v1 to v2 migration uses. A link on a question with no
    such target counts as unmatched: nothing has carried it over. The count runs in the
    database, so auditing the largest consultations loads no rows into memory.
    """
    links = Response.chosen_options.through.objects.filter(
        response__question__consultation=consultation
    ).annotate(
        # No branch for demographic questions: a selected option there has no row to match,
        # so it stays unmatched and the audit reports it
        target_question_id=Case(
            When(
                response__question__type=Question.QuestionType.CLOSED,
                then=F("response__question_id"),
            ),
            When(
                response__question__type=Question.QuestionType.OPEN,
                then=F("response__question__closed_question_id"),
            ),
        )
    )
    carried = Response.objects.filter(
        question_id=OuterRef("target_question_id"),
        respondent_id=OuterRef("response__respondent_id"),
        text=OuterRef("multichoiceanswer__text"),
    )
    return links.annotate(carried=Exists(carried)).filter(carried=False).count()
