"""Reconcile legacy multiple-choice links against the Response rows that replace them.

Reads the MultiChoiceAnswer and chosen_options tables, so this module goes when they do.
"""

from consultations.models import Consultation, Question, Response
from consultations.services.migrate_v1_to_v2 import option_target_question_id


def count_unmatched_legacy_answers(consultation: Consultation) -> int:
    """Selected options with no Response row on the question that should hold them.

    The target is the question itself when it is closed and its closed sibling when it
    is open, the same mapping the v1 to v2 migration uses. A link on a question with no
    such target counts as unmatched: nothing has carried it over.
    """
    questions = {question.id: question for question in consultation.question_set.all()}
    existing_rows = set(
        Response.objects.filter(
            question__consultation=consultation, question__type=Question.QuestionType.CLOSED
        ).values_list("question_id", "respondent_id", "text")
    )

    links = (
        Response.chosen_options.through.objects.filter(
            response__question__consultation=consultation
        )
        .values_list("response__question_id", "response__respondent_id", "multichoiceanswer__text")
        .iterator(chunk_size=1000)
    )
    unmatched = 0
    for source_question_id, respondent_id, option_text in links:
        target_id = option_target_question_id(questions[source_question_id])
        if target_id is None or (target_id, respondent_id, option_text) not in existing_rows:
            unmatched += 1
    return unmatched
