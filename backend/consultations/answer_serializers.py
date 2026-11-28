from consultations.services.closed_answers import count_option_responses, list_selected_texts


class AnswerCountsMixin:
    """A question's selectable answers with how many respondents chose each."""

    def get_multiple_choice_answer(self, obj) -> list[dict]:
        counts = getattr(obj, "prefetched_option_counts", None)
        if counts is None:
            counts = count_option_responses(obj)
        # An option has no record of its own, so its text is the id the frontend filters by
        return [{"id": item["text"], **item} for item in counts]


class SelectedAnswersMixin:
    """The answers one respondent selected on a response's question."""

    def get_multiple_choice_answer(self, obj) -> list[str]:
        answers_question_id = obj.question.answers_question_id
        if answers_question_id is None:
            return []
        closed_answers = getattr(obj.respondent, "prefetched_closed_answers", None)
        if closed_answers is None:
            return list_selected_texts(obj.question, [obj.respondent_id]).get(obj.respondent_id, [])
        return [
            answer.text for answer in closed_answers if answer.question_id == answers_question_id
        ]
