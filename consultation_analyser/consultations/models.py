import datetime
import uuid

import faker as _faker
import pydantic
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.db import models
from django.utils.text import slugify
from simple_history.models import HistoricalRecords

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import public_schema

faker = _faker.Faker()


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


class SlugFromTextModel(models.Model):
    text = models.CharField(max_length=256)
    slug = models.SlugField(null=False, editable=False, max_length=256)

    def save(self, *args, **kwargs):
        # Generate a slug from the text - ensure unique by adding timestamp if needed.
        # Don't allow empty slug.
        ModelClass = self.__class__
        cropped_length = 220
        cropped_text = self.text[:cropped_length]
        generated_slug = slugify(cropped_text)
        if self.pk:
            slug_exists = (
                ModelClass.objects.filter(slug=generated_slug).exclude(pk=self.pk).exists()
            )
        else:
            slug_exists = ModelClass.objects.filter(slug=generated_slug).exists()
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")
        if not generated_slug:
            generated_slug = timestamp
        elif slug_exists:
            generated_slug = f"{generated_slug}-{timestamp}"
        self.slug = generated_slug
        return super().save(*args, **kwargs)

    class Meta:
        abstract = True


class Consultation(UUIDPrimaryKeyModel, TimeStampedModel, SlugFromTextModel):
    users = models.ManyToManyField(User)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta, SlugFromTextModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="unique_consult_slug"),
        ]


# TODO - add QuestionGroup - to aggregate questions that should appear together


class Question(UUIDPrimaryKeyModel, TimeStampedModel, SlugFromTextModel):
    text = models.TextField()
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    order = models.IntegerField(null=True)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta, SlugFromTextModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="unique_q_slug"),
        ]


class QuestionPart(UUIDPrimaryKeyModel, TimeStampedModel):
    class QuestionType(models.TextChoices):
        FREE_TEXT = "free_text"
        SINGLE_OPTION = "single_option"
        MULTIPLE_OPTIONS = "multiple_options"

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()
    type = models.CharField(max_length=16, choices=QuestionType.choices)
    options = models.JSONField(default=list)
    order = models.IntegerField(null=True)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


# TODO - add ExpandedQuestionPart


class Respondent(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    # demographic data, or anything else that is at respondent level
    data = models.JSONField(default=dict)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class Answer(UUIDPrimaryKeyModel, TimeStampedModel):
    question_part = models.ForeignKey(QuestionPart, on_delete=models.CASCADE)
    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE)
    text = models.TextField()
    chosen_options = models.JSONField(default=list)
    # TODO - add favourite

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class ExecutionRun(UUIDPrimaryKeyModel, TimeStampedModel):
    class TaskType(models.TextChoices):
        SENTIMENT_ANALYSIS = "sentiment_analysis"
        THEME_GENERATION = "theme_generation"
        THEME_MAPPING = "theme_mapping"

    type = models.CharField(max_length=32, choices=TaskType.choices)
    # TODO - add metadata e.g. langfuse_id
    # Note, the execution run will be run on responses to a particular
    # question part - but this will be stored in the correspondong framework/mapping etc.
    history = HistoricalRecords()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class Framework(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    A Framework groups a set of themes, that are them used to
    classify consultation responses.
    Create a new Framework every time the set of themes changes.
    """

    execution_run = models.ForeignKey(ExecutionRun, on_delete=models.CASCADE, null=True)
    question_part = models.ForeignKey(QuestionPart, on_delete=models.CASCADE)
    # When Framework is created - record reason it was changed & user that created it
    change_reason = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # None when AI generated
    precursor = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    def amend_framework(self, user: User, change_reason: str) -> "Framework":
        """
        Creates a new Framework object based on the existing framework.
        This allows us to track history and changes of a framework.
        """
        new_framework = Framework.objects.create(
            execution_run=None, question_part=self.question_part, user=user, change_reason=change_reason, precursor=self,
        )
        # Only have execution_run when we AI generate framework
        return new_framework

    def get_themes_removed_from_previous_framework(self) -> models.QuerySet:
        """Themes removed from the previous framework i.e. no longer exist in any format."""
        if not self.precursor:
            return self.theme_set.none()

        themes_in_this_framework = self.theme_set.all()
        themes_that_persisted = themes_in_this_framework.values_list("precursor__id", flat=True)
        precursor_themes_removed = self.precursor.theme_set.exclude(id__in=themes_that_persisted)
        return precursor_themes_removed

    def get_themes_added_to_previous_framework(self) -> models.QuerySet:
        """
        Themes that were added in this framework, and didn't exist in
        the previous framework.
        """
        if not self.precursor:
            return self.theme_set.all()

        previous_framework_themes = self.precursor.theme_set.values_list("id", flat=True)
        new_themes = self.themes_set.exclude(precursor__id__in=previous_framework_themes)
        return new_themes


class Theme(UUIDPrimaryKeyModel, TimeStampedModel):
    # The new theme is assigned to a new framework with the change reason and user.
    # The theme that it has been changed from is the precursor.
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE)
    precursor = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    # TODO - add theme_code which comes from pipeline run
    name = models.CharField(max_length=256)  # TODO - is this long enough
    description = models.TextField()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    def amend_theme(self, new_framework: Framework, **kwargs) -> "Theme":
        """
        Creates a new Theme object based on the existing theme.
        This allows us to track history and changes of a theme.
        """
        new_theme = Theme.objects.create(framework=new_framework, precursor=self)
        for field in self._meta.get_fields():
            field_name = field.name
            if field_name not in ["id", "precursor", "framework"]:
                # Get updated value if exists, else use value from existing theme.
                value = kwargs.get(field_name, getattr(self, field_name))
                setattr(new_theme, field.name, value)
                new_theme.save()
        return new_theme


class ThemeMapping(UUIDPrimaryKeyModel, TimeStampedModel):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    reason = models.TextField()
    execution_run = models.ForeignKey(ExecutionRun, on_delete=models.CASCADE)

    history = HistoricalRecords()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    @staticmethod
    def get_latest_theme_mappings_for_question_part(part: QuestionPart) -> models.QuerySet:
        """
        Get the set of the theme mappings corresponding to the latest execution run.
        """
        theme_mappings_for_question_part = ThemeMapping.objects.filter(answer__question_part=part)
        execution_runs = ExecutionRun.objects.filter(
            thememapping__in=theme_mappings_for_question_part
        ).distinct()
        latest_execution_run = execution_runs.order_by("created_at").last()
        if latest_execution_run:
            latest_mappings = ThemeMapping.objects.filter(execution_run=latest_execution_run)
        else:
            latest_mappings = ThemeMapping.objects.none()
        return latest_mappings


class SentimentMapping(UUIDPrimaryKeyModel, TimeStampedModel):
    class PositionType(models.TextChoices):
        AGREE = "Agree"
        DISAGREE = "Disagree"
        UNCLEAR = "Unclear"

    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    execution_run = models.ForeignKey(ExecutionRun, on_delete=models.CASCADE)
    position = models.CharField(max_length=16, choices=PositionType.choices)

    history = HistoricalRecords()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass
