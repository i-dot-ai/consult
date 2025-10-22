import uuid
from textwrap import shorten

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.validators import BaseValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from pgvector.django import VectorField
from simple_history.models import HistoricalRecords

from consultation_analyser.authentication.models import User


# TODO: we don't use this anymore, remove it without manage.py makemigrations complaining
class MultipleChoiceSchemaValidator(BaseValidator):
    def compare(self, value, _limit_value):
        pass


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


class ConsultationStage(models.TextChoices):
    THEME_SIGN_OFF = "theme_sign_off", "Theme Sign Off"
    ANALYSIS = "analysis", "Analysis"


class Consultation(UUIDPrimaryKeyModel, TimeStampedModel):  # type: ignore
    title = models.CharField(max_length=256)
    users = models.ManyToManyField(User)
    stage = models.CharField(
        max_length=32,
        choices=ConsultationStage.choices,
        default=ConsultationStage.ANALYSIS,
    )
    code = models.SlugField(max_length=256, null=True, blank=True)

    def __str__(self):
        return shorten(self.code or "undefined", width=64, placeholder="...")


class Question(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    Combined question model - can have free text, multiple choice, or both.
    Replaces the Question/QuestionPart split.
    """

    class ThemeStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"

    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    text = models.TextField()
    number = models.IntegerField()
    theme_status = models.CharField(
        max_length=32, choices=ThemeStatus.choices, default=ThemeStatus.CONFIRMED
    )

    # Question configuration
    has_free_text = models.BooleanField(default=True)
    has_multiple_choice = models.BooleanField(default=False)
    total_responses = models.IntegerField(
        default=0,
        help_text="Number of free text responses for this question",
        null=True,
        blank=True,
    )

    @property
    def multiple_choice_options(self) -> list:
        """List of options when has_multiple_choice=True"""
        return list(self.multichoiceanswer_set.all())

    @property
    def proportion_of_audited_answers(self) -> float:
        """Calculate proportion of human-reviewed responses for free text questions"""
        if not self.has_free_text:
            return 0

        # Count total responses with free text
        total_responses = self.response_set.filter(
            free_text__isnull=False, free_text__gt=""
        ).count()

        if total_responses == 0:
            return 0

        # Count human-reviewed responses
        reviewed_responses = self.response_set.filter(
            free_text__isnull=False, free_text__gt="", annotation__human_reviewed=True
        ).count()

        return reviewed_responses / total_responses

    def update_total_responses(self):
        """Update the total_responses count based on current free text responses"""
        if self.has_free_text:
            count = self.response_set.filter(free_text__isnull=False, free_text__gt="").count()
            self.total_responses = count
            self.save(update_fields=["total_responses"])
        else:
            self.total_responses = 0
            self.save(update_fields=["total_responses"])

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["consultation", "number"], name="unique_question_number"
            ),
        ]
        ordering = ["number"]
        indexes = [
            models.Index(fields=["consultation", "has_free_text"]),
        ]

    def __str__(self):
        return shorten(self.text, width=64, placeholder="...")


class Respondent(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, editable=False)
    themefinder_id = models.IntegerField(null=True, blank=True, editable=False)
    demographics = models.ManyToManyField("DemographicOption", blank=True)
    name = models.TextField(null=True, blank=True)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        indexes = [
            models.Index(fields=["consultation", "themefinder_id"]),
        ]

    @property
    def identifier(self):
        return self.themefinder_id if self.themefinder_id else self.id


class Response(UUIDPrimaryKeyModel, TimeStampedModel):
    """Response to a question - can include both free text and multiple choice"""

    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # Response content
    free_text = models.TextField(null=True, blank=True)  # Free text response
    chosen_options = models.ManyToManyField("MultiChoiceAnswer", blank=True)
    embedding = VectorField(dimensions=settings.EMBEDDING_DIMENSION, null=True, blank=True)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["respondent", "question"], name="unique_question_response"
            ),
        ]
        indexes = [
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self):
        if self.free_text:
            return shorten(self.free_text, width=64, placeholder="...")
        return "multi-choice response"


@receiver(post_save, sender=Response)
def update_search_vector(sender, instance, created, **kwargs):
    # Avoid infinite recursion
    if "search_vector" in (kwargs.get("update_fields") or []):
        return

    # Update the search vector
    Response.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector("free_text", config="english")
    )


class DemographicOption(UUIDPrimaryKeyModel, TimeStampedModel):
    """Normalized storage of demographic field options for efficient querying across pages"""

    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=128)
    field_value = models.JSONField()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["consultation", "field_name", "field_value"],
                name="unique_demographic_option",
            ),
        ]
        indexes = [
            models.Index(fields=["consultation", "field_name"]),
        ]

    def __str__(self):
        return f"{self.field_name}={self.field_value}"


class SelectedTheme(UUIDPrimaryKeyModel, TimeStampedModel):
    """Themes that have been selected during / after theme sign-off"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    name = models.TextField()
    description = models.TextField()
    key = models.CharField(max_length=128, null=True, blank=True)
    crosscuttingtheme = models.ForeignKey(
        "CrossCuttingTheme", on_delete=models.CASCADE, null=True, blank=True
    )
    version = models.IntegerField(default=1)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["question", "key"],
                name="unique_theme",
                condition=models.Q(key__isnull=False),
            ),
        ]
        indexes = [
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return self.name


class CandidateTheme(UUIDPrimaryKeyModel, TimeStampedModel):
    """AI-generated (candidate) themes for a question"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    name = models.TextField()
    description = models.TextField()
    approximate_frequency = models.IntegerField(null=True, blank=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    selectedtheme = models.OneToOneField(
        SelectedTheme, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        indexes = [
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return self.name


class CrossCuttingTheme(UUIDPrimaryKeyModel, TimeStampedModel):
    """Cross-cutting themes that encompass multiple regular themes across a consultation"""

    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="cross_cutting_themes"
    )
    name = models.CharField(max_length=256)
    description = models.TextField()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["consultation", "name"],
                name="unique_cross_cutting_theme",
            ),
        ]

    def __str__(self):
        return self.name


class ResponseAnnotationTheme(UUIDPrimaryKeyModel, TimeStampedModel):
    """Through model to track original AI vs human-reviewed theme assignments"""

    response_annotation = models.ForeignKey("ResponseAnnotation", on_delete=models.CASCADE)
    theme = models.ForeignKey(SelectedTheme, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )  # None for AI, User for human

    history = HistoricalRecords()

    def is_original_ai_assignment(self) -> bool:
        return self.assigned_by is None

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "response_annotation",
                    "theme",
                ],
                name="unique_theme_assignment",
            ),
        ]


class ResponseAnnotation(UUIDPrimaryKeyModel, TimeStampedModel):
    """AI outputs and human reviews for a response"""

    class Sentiment(models.TextChoices):
        AGREEMENT = "AGREEMENT", "Agreement"
        DISAGREEMENT = "DISAGREEMENT", "Disagreement"
        UNCLEAR = "UNCLEAR", "Unclear"

    response = models.OneToOneField(Response, on_delete=models.CASCADE, related_name="annotation")

    # AI-generated outputs (only for free text responses)
    themes = models.ManyToManyField(SelectedTheme, through=ResponseAnnotationTheme, blank=True)
    sentiment = models.CharField(max_length=12, choices=Sentiment.choices, null=True, blank=True)
    evidence_rich = models.BooleanField(default=False, null=True, blank=True)

    # Human review tracking
    human_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    flagged_by = models.ManyToManyField(to=User, blank=True, related_name="flagged_by")

    # History tracking
    history = HistoricalRecords()

    @property
    def is_edited(self) -> bool:
        """has this annotation ever been changed?"""
        if self.history.count() > 1:
            return True

        # have associated themes ever been changed by a human?
        return ResponseAnnotationTheme.history.filter(
            response_annotation=self,
            assigned_by__isnull=False,
        ).exists()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        indexes = [
            models.Index(fields=["human_reviewed"]),
            models.Index(fields=["sentiment"]),
            models.Index(fields=["evidence_rich"]),
        ]

    def mark_human_reviewed(self, user):
        """Helper method to mark as human reviewed"""
        self.human_reviewed = True
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save()

    def add_original_ai_themes(self, themes):
        """Add themes as original AI assignments"""
        for theme in themes:
            ResponseAnnotationTheme.objects.get_or_create(
                response_annotation=self,
                theme=theme,
                defaults={"assigned_by": None},
            )

    def set_human_reviewed_themes(self, themes, user):
        """Set themes as human-reviewed, will override original AI assignments"""
        # Remove existing user-assigned theme assignments

        current_theme_ids = {x.theme_id for x in self.responseannotationtheme_set.all()}
        proposed_theme_ids = {x.id for x in themes}

        self.responseannotationtheme_set.filter(
            theme_id__in=current_theme_ids - proposed_theme_ids
        ).delete()

        for theme_id in proposed_theme_ids - current_theme_ids:
            ResponseAnnotationTheme.objects.create(
                response_annotation=self,
                theme_id=theme_id,
                assigned_by=user,
            )

    def get_original_ai_themes(self):
        """Get themes assigned by AI
        Note that this implementation makes an implicit assumption that the AI only assigns the themes once
        """
        theme_ids = ResponseAnnotationTheme.history.filter(
            response_annotation=self,
            history_type="+",
            assigned_by__isnull=True,
        ).values_list("theme_id", flat=True)
        return SelectedTheme.objects.filter(id__in=theme_ids)

    def get_current_themes(self):
        """Get latest themes assigned by any human or AI"""
        return self.themes.distinct()

    def save(self, *args, **kwargs) -> None:
        """
        Override save to prevent accidental direct theme manipulation.
        Themes should be added using add_original_ai_themes() or set_human_reviewed_themes().
        """
        # Check if themes are being passed via save (which shouldn't happen)
        if "themes" in kwargs:
            raise ValueError(
                "Direct theme assignment through save() is not allowed. "
                "Use add_original_ai_themes() or set_human_reviewed_themes() instead."
            )

        super().save(*args, **kwargs)


class MultiChoiceAnswer(UUIDPrimaryKeyModel, TimeStampedModel):  # type: ignore[misc]
    """a possible answer to a multi choice question"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return f"{self.question.number} = {self.text}"
