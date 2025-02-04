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


class Consultation(UUIDPrimaryKeyModel, TimeStampedModel):
    title = models.CharField(max_length=256)
    slug = models.SlugField(null=False, editable=False, max_length=256)
    users = models.ManyToManyField(User)

    def save(self, *args, **kwargs):
        # Generate slug from text - if needed, append integer for uniqueness.
        def slug_exists_for_another_consultation(self, slug):
            if self.slug == slug:
                return False
            return Consultation.objects.filter(slug=slug).exists()

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


class Question(UUIDPrimaryKeyModel, TimeStampedModel):
    text = models.TextField()
    slug = models.SlugField(null=False, editable=False, max_length=256)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    number = models.IntegerField(null=False, default=0)

    def save(self, *args, **kwargs):
        # Generate slug from text - if needed, add question number for uniqueness.
        # if needed (usually won't be). Don't allow empty slug.
        cropped_length = 256
        generated_slug = slugify(self.text)[:cropped_length]
        if self.pk:
            slug_exists = (
                Question.objects.filter(slug=generated_slug)
                .filter(consultation=self.consultation)
                .exclude(pk=self.pk)
                .exists()
            )
        else:
            slug_exists = (
                Question.objects.filter(slug=generated_slug)
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


class QuestionPart(UUIDPrimaryKeyModel, TimeStampedModel):
    class QuestionType(models.TextChoices):
        FREE_TEXT = "free_text"
        SINGLE_OPTION = "single_option"
        MULTIPLE_OPTIONS = "multiple_options"

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
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
    is_theme_mapping_audited = models.BooleanField(default=False)
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
            return self.theme_set.none()
        themes_in_this_framework = self.theme_set.all()
        precursors_themes_that_persisted = themes_in_this_framework.values_list(
            "precursor__id", flat=True
        )
        persisted_ids = [id for id in precursors_themes_that_persisted if id]  # remove None
        precursor_themes_removed = self.precursor.theme_set.exclude(id__in=persisted_ids).distinct()
        return precursor_themes_removed

    def get_themes_added_to_previous_framework(self) -> models.QuerySet:
        """
        Themes that were added in this framework, and didn't exist in
        the previous framework.
        """
        if not self.precursor:
            return self.theme_set.all()

        previous_framework_themes = self.precursor.theme_set.values_list("id", flat=True)
        new_themes = self.theme_set.exclude(precursor__id__in=previous_framework_themes)
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

    def save(self, *args, **kwargs):
        raise ValueError("Direct save() method is not allowed for Themes - use custom methods.")

    @classmethod
    def create_initial_theme(cls, framework: Framework, name: str, description: str) -> "Theme":
        """Create initial theme for a framework."""
        new_theme = Theme(framework=framework, name=name, description=description, precursor=None)
        super(Theme, new_theme).save()
        return new_theme

    def create_descendant_theme(
        self, new_framework: Framework, name: str, description: str
    ) -> "Theme":
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
        new_theme = Theme(
            precursor=self,
            name=name,
            description=description,
            framework=new_framework,
        )
        super(Theme, new_theme).save()
        return new_theme


class ThemeMapping(UUIDPrimaryKeyModel, TimeStampedModel):
    # When changing the mapping for an answer, don't change the answer
    # change the theme.
    class Stance(models.TextChoices):
        POSITIVE = "POSITIVE", "Positive"
        NEGATIVE = "NEGATIVE", "Negative"

    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    reason = models.TextField()
    execution_run = models.ForeignKey(ExecutionRun, on_delete=models.CASCADE, null=True)
    stance = models.CharField(max_length=8, choices=Stance.choices)
    history = HistoricalRecords()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    @staticmethod
    def get_latest_theme_mappings_for_question_part(part: QuestionPart) -> models.QuerySet:
        """
        Get the set of the theme mappings corresponding to the latest execution run.
        The latest will include all changes that have been made manually to mapping
        (changes stored in history table).
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
