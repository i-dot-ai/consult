import uuid
from dataclasses import dataclass

import pydantic
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.db import models

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import public_schema


class MultipleChoiceSchemaValidator(BaseValidator):
    def compare(self, value, _limit_value):
        if not value:
            return
        try:
            public_schema.MultipleChoice(value)
        except pydantic.ValidationError as e:
            raise ValidationError(e.json())


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
    users = models.ManyToManyField(User)

    def has_themes(self):
        return OldTheme.objects.filter(answer__question__section__consultation=self).exists()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="unique_consultation_slug"),
        ]

    def delete(self, *args, **kwargs):
        """
        Delete Related theme objects that can become orphans
        because deletes will not cascade from Answer because
        the Theme in question could still be associated with
        another Answer
        """
        OldTheme.objects.filter(answer__question__section__consultation=self).delete()

        super().delete(*args, **kwargs)


class Section(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    name = models.TextField()
    slug = models.CharField(null=False, max_length=256)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "consultation"], name="unique_section_consultation"
            ),
        ]


class Question(UUIDPrimaryKeyModel, TimeStampedModel):
    text = models.CharField(
        null=False, max_length=None
    )  # no idea what's a sensible value for max_length
    slug = models.CharField(null=False, max_length=256)
    has_free_text = models.BooleanField(default=False)
    multiple_choice_options = models.JSONField(
        null=True, blank=True, validators=[MultipleChoiceSchemaValidator(limit_value=None)]
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    @dataclass
    class MultipleChoiceResponseCount:
        answer: str
        count: int
        percent: float

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug", "section"], name="unique_question_section"),
        ]

    @property
    def latest_themes(self):
        try:
            latest_processing_run = ProcessingRun.objects.filter(consultation=self.section.consultation).order_by("created_at").last()
            latest_themes = Theme.objects.filter(topic_model__processing_run=latest_processing_run).filter(topic_model__question=self)
            return latest_themes
        except ProcessingRun.DoesNotExist: # TODO - remove OldTheme in future
            old_theme_ids = self.answer_set.values_list("old_theme__id", flat=True)
            return OldTheme.objects.filter(id__in=old_theme_ids)


class ConsultationResponse(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(editable=False, null=False)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class ProcessingRun(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    # TODO - add more processing run metadata

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class TopicModelMetadata(UUIDPrimaryKeyModel, TimeStampedModel):
    processing_run = models.ForeignKey(ProcessingRun, on_delete=models.CASCADE)
    # Question needed for uniqueness constraint
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    # TODO -  Some other metadata on the model TBC and link to saved model

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["processing_run", "question"], name="unique_topic_model_question_run"
            ),
        ]


class Theme(UUIDPrimaryKeyModel, TimeStampedModel):
    # Topic model, keywords and ID come from BERTopic
    topic_model_metadata = models.ForeignKey(
        TopicModelMetadata, on_delete=models.CASCADE, null=True
    )
    topic_keywords = models.JSONField(default=list)
    topic_id = models.IntegerField(null=True)  # Topic ID from BERTopic
    is_outlier = models.GeneratedField(
        expression=models.Q(topic_id=-1), output_field=models.BooleanField(), db_persist=True
    )
    # LLM generates short_description and summary
    short_description = models.TextField(blank=True)
    summary = models.TextField(blank=True)  # More detailed description

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["topic_id", "topic_model_metadata"], name="unique_id_per_model"
            ),
        ]


# TODO - Here for legacy reasons, can be deleted once we are using processing run approach
class OldTheme(UUIDPrimaryKeyModel, TimeStampedModel):
    # LLM generates short_description and summary
    short_description = models.TextField(blank=True)
    summary = models.TextField(blank=True)  # More detailed description
    # Duplicates info in Answer model, but needed for uniqueness constraint.
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    # Topic keywords and ID come from BERTopic
    topic_keywords = models.JSONField(default=list)
    topic_id = models.IntegerField(null=True)  # Topic ID from BERTopic
    is_outlier = models.GeneratedField(
        expression=models.Q(topic_id=-1), output_field=models.BooleanField(), db_persist=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["topic_id", "question"], name="unique_up_to_question"),
        ]


class AnswerQuerySet(models.QuerySet):
    MULTIPLE_CHOICE_QUERY = """
        EXISTS (
            SELECT 1
            FROM jsonb_array_elements(multiple_choice) AS elem,
                 jsonb_array_elements_text(elem -> 'options') AS opt
            WHERE elem ->> 'question_text' = %s
              AND opt = %s
        )
    """

    def filter_multiple_choice(self, question, answer):
        return self.extra(where=[self.MULTIPLE_CHOICE_QUERY], params=[question, answer])  # nosec


class Answer(UUIDPrimaryKeyModel, TimeStampedModel):
    objects = AnswerQuerySet.as_manager()

    multiple_choice = models.JSONField(
        null=True, blank=True, validators=[MultipleChoiceSchemaValidator(limit_value=None)]
    )
    free_text = models.TextField(null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    consultation_response = models.ForeignKey(ConsultationResponse, on_delete=models.CASCADE)
    old_theme = models.ForeignKey(
        OldTheme, on_delete=models.SET_NULL, null=True, blank=True
    )  # Legacy themes, soon won't be needed when we move to processing runs
    themes = models.ManyToManyField(Theme)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    def save_theme_to_answer(self, topic_keywords: list, topic_id: int, topic_model_metadata: TopicModelMetadata):
        theme, _ = Theme.objects.get_or_create(
            topic_keywords=topic_keywords, topic_id=topic_id, topic_model_metadata=topic_model_metadata
        )
        self.themes.add(theme)
        self.save()

    @property
    def latest_theme(self):
        # Get the theme from the latest processing run, may be none if there was no theme for this response.
        # If no processing runs - check for 'OldThemes' - in future this can be deleted when we use processing runs for everything.
        consultation = self.question.section.consultation
        try:
            latest_processing_run = ProcessingRun.objects.filter(consultation=consultation).order_by("created_at").last()
        except ProcessingRun.DoesNotExist:
            return self.old_theme #TODO - remove in future
        try:
            latest = self.themes.get(topic_model_metadata__processing_run=latest_processing_run)
        except Theme.DoesNotExist:
            latest = None
        return latest

