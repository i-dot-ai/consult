import datetime
import uuid
from collections import Counter, OrderedDict
from enum import Enum

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


# TODO: we don't use this anymore, remove it without manage.py makemigrations complaining
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
        # Generate slug from text - ensure unique by adding timestamp
        # if needed (usually won't be). Don't allow empty slug.
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


# TODO - old model to be deleted
class ConsultationOld(UUIDPrimaryKeyModel, TimeStampedModel):
    title = models.CharField(max_length=256)
    slug = models.SlugField(null=False, editable=False, max_length=256)
    users = models.ManyToManyField(User)

    def save(self, *args, **kwargs):
        # Generate slug from text - if needed, append integer for uniqueness.
        def slug_exists_for_another_consultation(self, slug):
            if self.slug == slug:
                return False
            return ConsultationOld.objects.filter(slug=slug).exists()

        cropped_length = 256
        slugified_title = slugify(self.title)[:cropped_length]

        i = 2
        generated_slug = slugified_title
        slug_exists = slug_exists_for_another_consultation(self, generated_slug)
        while slug_exists:
            str_to_append = f"-{i}"
            n = len(str_to_append)
            generated_slug = f"{slugified_title[: (cropped_length - n)]}{str_to_append}"
            i = i + 1
            slug_exists = slug_exists_for_another_consultation(self, generated_slug)

        self.slug = generated_slug
        return super().save(*args, **kwargs)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="unique_consult_slug"),
        ]


# TODO - old model to be deleted
class QuestionOld(UUIDPrimaryKeyModel, TimeStampedModel):
    text = models.TextField()
    slug = models.SlugField(null=False, editable=False, max_length=256)
    consultation = models.ForeignKey(ConsultationOld, on_delete=models.CASCADE, db_index=False)
    number = models.IntegerField(null=False, default=0)

    def save(self, *args, **kwargs):
        # Generate slug from text - if needed, add question number for uniqueness.
        # if needed (usually won't be). Don't allow empty slug.
        cropped_length = 256
        generated_slug = slugify(self.text)[:cropped_length]
        if self.pk:
            slug_exists = (
                QuestionOld.objects.filter(slug=generated_slug)
                .filter(consultation=self.consultation)
                .exclude(pk=self.pk)
                .exists()
            )
        else:
            slug_exists = (
                QuestionOld.objects.filter(slug=generated_slug)
                .filter(consultation=self.consultation)
                .exists()
            )
        if not generated_slug:
            generated_slug = str(self.number)
        elif slug_exists:
            str_to_append = f"-{str(self.number)}"
            n = len(str_to_append)
            generated_slug = f"{generated_slug[: (cropped_length - n)]}{str_to_append}"
        self.slug = generated_slug
        return super().save(*args, **kwargs)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["consultation", "slug"], name="unique_q_slug"),
            models.UniqueConstraint(fields=["consultation", "number"], name="unique_q_number"),
        ]
        ordering = ["number"]
        indexes = [
            models.Index(fields=["consultation_id"], name="explicit_con_q"),
        ]  # This is going to be deleted anyway


# TODO - old model to be deleted
class QuestionPart(UUIDPrimaryKeyModel, TimeStampedModel):
    class QuestionType(models.TextChoices):
        FREE_TEXT = "free_text"
        SINGLE_OPTION = "single_option"
        MULTIPLE_OPTIONS = "multiple_options"

    question = models.ForeignKey(QuestionOld, on_delete=models.CASCADE)
    text = models.TextField()
    type = models.CharField(max_length=16, choices=QuestionType.choices)
    options = models.JSONField(null=True)  # List, null if free-text
    number = models.IntegerField(null=False, default=0)

    @property
    def proportion_of_audited_answers(self) -> float:
        # Only relevant for free text questions
        total_answers = self.answer_set.count()
        if total_answers == 0:
            return 0
        audited_answers = self.answer_set.filter(is_theme_mapping_audited=True).count()
        return audited_answers / total_answers

    def get_option_counts(self) -> OrderedDict:
        """
        Get the counts of each option chosen for the corresponding answers.
        Keep counts in the same order as specified in QuestionPart.options.
        """
        all_chosen_options = []

        for answer in self.answer_set.all():
            chosen_options = answer.chosen_options if answer.chosen_options else []
            all_chosen_options.extend(chosen_options)
        counts = Counter(all_chosen_options)

        all_possible_options = self.options or []
        # We may care about the order they appear
        ordered_counts = OrderedDict((option, counts[option]) for option in all_possible_options)
        return ordered_counts

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["question", "number"], name="unique_part_per_question"),
            models.UniqueConstraint(
                fields=["question"],
                condition=models.Q(type="free_text"),
                name="unique_free_text_per_question",
            ),
        ]
        # Assume at most one free_text part per question, that is what we expect from data we've seen to date
        ordering = ["number"]


# TODO - old model to be deleted
class RespondentOld(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(ConsultationOld, on_delete=models.CASCADE, db_index=False)
    # demographic data, or anything else that is at respondent level
    data = models.JSONField(default=dict)
    themefinder_respondent_id = models.IntegerField(null=True)
    user_provided_id = models.CharField(
        max_length=128, null=True
    )  # Optional response ID supplied by department

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        indexes = [
            models.Index(fields=["consultation_id"], name="explicit_con_respondent"),
        ]  # This is going to be deleted anyway

    @property
    def identifier(self) -> uuid.UUID | int:
        if self.themefinder_respondent_id:
            return self.themefinder_respondent_id
        return self.id


# TODO - old model to be deleted
class Answer(UUIDPrimaryKeyModel, TimeStampedModel):
    question_part = models.ForeignKey(QuestionPart, on_delete=models.CASCADE)
    respondent = models.ForeignKey(RespondentOld, on_delete=models.CASCADE)
    text = models.TextField()
    chosen_options = models.JSONField(default=list)
    is_theme_mapping_audited = models.BooleanField(default=False, null=True)

    history = HistoricalRecords()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    @property
    def datetime_theme_mapping_audited(self) -> datetime.datetime | None:
        if not self.is_theme_mapping_audited:
            return None

        # Use history to find the first date it was marked as audited
        history_for_answer = self.history.all().order_by("history_date")
        for historical_record in history_for_answer:
            if historical_record.is_theme_mapping_audited:
                return historical_record.modified_at
        return None


# TODO - old model to be deleted
class ExecutionRun(UUIDPrimaryKeyModel, TimeStampedModel):
    class TaskType(models.TextChoices):
        SENTIMENT_ANALYSIS = "sentiment_analysis"
        THEME_GENERATION = "theme_generation"
        THEME_MAPPING = "theme_mapping"
        EVIDENCE_EVALUATION = "evidence_evaluation"

    type = models.CharField(max_length=32, choices=TaskType.choices)
    # TODO - add metadata e.g. langfuse_id
    # Note, the execution run will be run on responses to a particular
    # question part - but this will be stored in the correspondong framework/mapping etc.

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


# TODO - old model to be deleted
class Framework(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    A Framework groups a set of themes, that are them used to
    classify consultation responses.
    Create a new Framework every time the set of themes changes.
    """

    # Execution run is the theme generation execution run that has generated the framework
    execution_run = models.ForeignKey(ExecutionRun, on_delete=models.CASCADE, null=True)
    question_part = models.ForeignKey(QuestionPart, on_delete=models.CASCADE)
    # When Framework is created - record reason it was changed & user that created it
    change_reason = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # None when AI generated
    precursor = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    def save(self, *args, **kwargs):
        raise ValueError("Direct save() method is not allowed for Frameworks - use custom methods.")

    @classmethod
    def create_initial_framework(
        cls, execution_run: ExecutionRun, question_part: QuestionPart
    ) -> "Framework":
        """Create initial framework for a question part."""
        # We require an execution run for the initial framework
        # user, change_reason, precursor are all None
        if not execution_run:
            raise ValueError("An initial Framework needs an execution run.")

        if execution_run.type != ExecutionRun.TaskType.THEME_GENERATION:
            raise ValueError("Initial framework must be based on theme generation")

        new_framework = Framework(
            execution_run=execution_run,
            question_part=question_part,
        )
        super(Framework, new_framework).save()
        return new_framework

    def create_descendant_framework(self, user: User, change_reason: str) -> "Framework":
        """
        Creates a new Framework object based on the existing framework.
        This allows us to track history and changes of a framework.
        Add themes manually.
        """
        new_framework = Framework(
            execution_run=None,
            question_part=self.question_part,
            user=user,
            change_reason=change_reason,
            precursor=self,
        )
        super(Framework, new_framework).save()
        # Only have execution_run when we AI generate framework
        return new_framework

    def get_themes_removed_from_previous_framework(self) -> models.QuerySet:
        """Themes removed from the previous framework i.e. no longer exist in any format."""
        if not self.precursor:
            return self.themeold_set.none()
        themes_in_this_framework = self.themeold_set.all()
        precursors_themes_that_persisted = themes_in_this_framework.values_list(
            "precursor__id", flat=True
        )
        persisted_ids = [id for id in precursors_themes_that_persisted if id]  # remove None
        precursor_themes_removed = self.precursor.themeold_set.exclude(
            id__in=persisted_ids
        ).distinct()
        return precursor_themes_removed

    def get_themes_added_to_previous_framework(self) -> models.QuerySet:
        """
        Themes that were added in this framework, and didn't exist in
        the previous framework.
        """
        if not self.precursor:
            return self.themeold_set.all()

        previous_framework_themes = self.precursor.themeold_set.values_list("id", flat=True)
        new_themes = self.themeold_set.exclude(precursor__id__in=previous_framework_themes)
        return new_themes

    def get_theme_mappings(self, history=False) -> models.QuerySet:
        if history:
            return ThemeMapping.history.filter(theme__framework=self)
        return ThemeMapping.objects.filter(theme__framework=self)


# TODO - old model to be deleted
class ThemeOld(UUIDPrimaryKeyModel, TimeStampedModel):
    # The new theme is assigned to a new framework with the change reason and user.
    # The theme that it has been changed from is the precursor.
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE)
    precursor = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    name = models.CharField(max_length=256)  # TODO - is this long enough
    description = models.TextField()
    key = models.CharField(max_length=128, null=True)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["framework", "key"], name="unique_framework_key"),
        ]

    def save(self, *args, **kwargs):
        raise ValueError("Direct save() method is not allowed for Themes - use custom methods.")

    @classmethod
    def create_initial_theme(
        cls, framework: Framework, name: str, description: str, key: str | None = None
    ) -> "ThemeOld":
        """Create initial theme for a framework."""
        new_theme = ThemeOld(
            framework=framework, name=name, description=description, key=key, precursor=None
        )
        super(ThemeOld, new_theme).save()
        return new_theme

    def create_descendant_theme(
        self,
        new_framework: Framework,
        name: str,
        description: str,
        key: str | None = None,
    ) -> "ThemeOld":
        """
        Creates a new Theme object based on the existing theme.
        Allows us to track history and changes of a theme.

        Args:
            self: The existing theme that we want to make changes to.
            new_framework: The new framework that the new theme will be assigned to.
                Should be based on the framework of the existing theme.
            **kwargs: Update the name, description etc.

        Returns:
            A new theme based on the existing theme, changed according to kwargs.
        """
        if self.framework != new_framework.precursor:
            raise ValueError(
                "Framework for new theme must be based on the framework for the existing theme."
            )
        new_theme = ThemeOld(
            precursor=self,
            name=name,
            description=description,
            framework=new_framework,
            key=key,
        )
        super(ThemeOld, new_theme).save()
        return new_theme

    def get_identifier(self) -> str:
        if self.key:
            return self.key
        return self.name


# TODO - old model to be deleted
class ThemeMapping(UUIDPrimaryKeyModel, TimeStampedModel):
    # When changing the mapping for an answer, don't change the answer
    # change the theme.
    class Stance(models.TextChoices, Enum):
        POSITIVE = "POSITIVE", "Positive"
        NEGATIVE = "NEGATIVE", "Negative"

    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    theme = models.ForeignKey(ThemeOld, on_delete=models.CASCADE)
    reason = models.TextField()
    # This is the theme mapping execution run
    # TODO - rename field to be more explicit, amend save to ensure correct type
    execution_run = models.ForeignKey(ExecutionRun, on_delete=models.CASCADE, null=True)
    stance = models.CharField(max_length=8, choices=Stance.choices, null=True)
    history = HistoricalRecords()
    user_audited = models.BooleanField(default=False)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["answer", "theme"], name="unique_theme_answer"),
        ]

    @classmethod
    def get_latest_theme_mappings(
        cls, question_part: QuestionPart, history: bool = False
    ) -> models.QuerySet:
        latest_framework = (
            Framework.objects.filter(question_part=question_part).order_by("created_at").last()
        )
        if latest_framework:
            return latest_framework.get_theme_mappings(history=history)
        if history:
            return ThemeMapping.history.none()
        return ThemeMapping.objects.none()


# TODO - old model to be deleted
class SentimentMapping(UUIDPrimaryKeyModel, TimeStampedModel):
    class Position(models.TextChoices, Enum):
        AGREEMENT = "AGREEMENT", "Agreement"
        DISAGREEMENT = "DISAGREEMENT", "Disagreement"
        UNCLEAR = "UNCLEAR", "Unclear"

    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    execution_run = models.ForeignKey(ExecutionRun, on_delete=models.CASCADE)
    position = models.CharField(max_length=12, choices=Position.choices)

    history = HistoricalRecords()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


# TODO - old model to be deleted
class EvidenceRichMapping(UUIDPrimaryKeyModel, TimeStampedModel):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    evidence_evaluation_execution_run = models.ForeignKey(ExecutionRun, on_delete=models.CASCADE)
    evidence_rich = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass
