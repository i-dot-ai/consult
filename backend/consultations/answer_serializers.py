from typing import ClassVar

from rest_framework import serializers

from consultations.models import MultiChoiceAnswer
from consultations.services.closed_answers import count_option_responses, list_selected_texts


class MultiChoiceAnswerSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    response_count = serializers.SerializerMethodField()

    def get_response_count(self, obj) -> int:
        # When filters are applied, the view annotates a dynamic count
        if hasattr(obj, "prefetched_response_count"):
            return obj.prefetched_response_count
        return obj.response_count

    class Meta:
        model = MultiChoiceAnswer
        fields: ClassVar[list] = ["id", "text", "response_count"]


class AnswerCountsMixin:
    """A question's selectable answers with how many respondents chose each."""

    def get_multiple_choice_answer(self, obj) -> list[dict]:
        if not obj.answers_from_responses:
            return MultiChoiceAnswerSerializer(obj.multichoiceanswer_set.all(), many=True).data
        counts = getattr(obj, "prefetched_option_counts", None)
        if counts is None:
            counts = count_option_responses(obj)
        # id mirrors text until the frontend keys answers by text
        return [{"id": item["text"], **item} for item in counts]


class SelectedAnswersMixin:
    """The answers one respondent selected on a response's question."""

    def get_multiple_choice_answer(self, obj) -> list[str]:
        if not obj.question.answers_from_responses:
            return [option.text for option in obj.chosen_options.all()]
        answers_question_id = obj.question.answers_question_id
        if answers_question_id is None:
            return []
        closed_answers = getattr(obj.respondent, "prefetched_closed_answers", None)
        if closed_answers is None:
            return list_selected_texts(obj.question, [obj.respondent_id]).get(obj.respondent_id, [])
        return [
            answer.text for answer in closed_answers if answer.question_id == answers_question_id
        ]
