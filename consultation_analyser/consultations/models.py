import uuid
from collections import Counter
from dataclasses import dataclass
from functools import reduce

from django.db import models


class UUIDPrimaryKeyModel(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    modified_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        abstract = True
        ordering = ["created_at"]


class Consultation(UUIDPrimaryKeyModel, TimeStampedModel):
    name = models.CharField(max_length=256)
    slug = models.CharField(null=False, max_length=256)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class Section(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    name = models.TextField()
    slug = models.CharField(null=False, max_length=256)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["slug", "consultation"], name="unique_section_consultation"),
        ]


class Question(UUIDPrimaryKeyModel, TimeStampedModel):
    text = models.CharField(null=False, max_length=None)  # no idea what's a sensible value for max_length
    slug = models.CharField(null=False, max_length=256)
    has_free_text = models.BooleanField(default=False)
    multiple_choice_options = models.JSONField(null=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    @dataclass
    class MultipleChoiceResponseCount:
        answer: str
        count: int
        percent: float

    def multiple_choice_response_counts(self) -> list[MultipleChoiceResponseCount]:
        if not self.multiple_choice_options:
            return []

        responses: list = reduce(
            lambda resps, answer: resps + answer.multiple_choice_responses, self.answer_set.all(), []
        )
        counter = Counter(responses)

        # this does not support more than one choice per response
        total_response_count = len(responses)
        response_counts = []
        for answer, count in counter.items():
            percent = round((count / total_response_count) * 100)
            response_counts.append(self.MultipleChoiceResponseCount(answer=answer, count=count, percent=percent))

        return response_counts

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug", "section"], name="unique_question_section"),
        ]


class ConsultationResponse(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class Theme(UUIDPrimaryKeyModel, TimeStampedModel):
    label = models.CharField(max_length=256, blank=True)
    summary = models.TextField(blank=True)
    keywords = models.JSONField(default=list)
    # Duplicates info in Answer model, but needed for uniqueness constraint.
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    is_outlier = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["label", "question"], name="unique_up_to_question"),
        ]

    def save(self, *args, **kwargs):
        label_constituents = self.label.split("_")
        self.keywords = label_constituents[1:]
        topic_number = label_constituents[0]
        self.is_outlier = topic_number == "-1"
        super.save(*args, **kwargs)


class Answer(UUIDPrimaryKeyModel, TimeStampedModel):
    multiple_choice_responses = models.JSONField(null=True)  # Multiple choice can have more than one response
    free_text = models.TextField(null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    consultation_response = models.ForeignKey(ConsultationResponse, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, null=True)  # For now, just one theme per answer

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    def save_theme_to_answer(self, theme_label, theme_keywords):
        question = self.question
        theme, _ = Theme.objects.get_or_create(
            question=question,
            label=theme_label,
            keywords=theme_keywords,
        )
        self.theme = theme
        self.save()
