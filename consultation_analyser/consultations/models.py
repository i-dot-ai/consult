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
from django.utils.text import slugify
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


class Consultation(UUIDPrimaryKeyModel, TimeStampedModel):
    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=256, unique=True)
    users = models.ManyToManyField(User)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:250]
            slug = base_slug
            counter = 1
            while Consultation.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        return super().save(*args, **kwargs)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="unique_consultation_slug"),
        ]

    def __str__(self):
        return shorten(self.slug, width=64, placeholder="...")


class Question(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    Combined question model - can have free text, multiple choice, or both.
    Replaces the Question/QuestionPart split.
    """

    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    text = models.TextField()
    slug = models.SlugField(max_length=256)
    number = models.IntegerField()

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

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.text)[:240]
            self.slug = f"{base_slug}-{self.number}" if base_slug else str(self.number)
        return super().save(*args, **kwargs)

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
            models.UniqueConstraint(fields=["consultation", "slug"], name="unique_question_slug"),
            models.UniqueConstraint(
                fields=["consultation", "number"], name="unique_question_number"
            ),
        ]
        ordering = ["number"]
        indexes = [
            models.Index(fields=["consultation", "has_free_text"]),
        ]

    def __str__(self):
        return shorten(self.slug, width=64, placeholder="...")


class Respondent(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    themefinder_id = models.IntegerField(null=True, blank=True)
    demographics = models.ManyToManyField("DemographicOption", blank=True)


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


class Theme(UUIDPrimaryKeyModel, TimeStampedModel):
    """AI-generated themes for a question (only for free text parts)"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    description = models.TextField()
    key = models.CharField(max_length=128, null=True, blank=True)
    parent = models.ForeignKey("CrossCuttingTheme", on_delete=models.CASCADE, null=True, blank=True)

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
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    is_original_ai_assignment = models.BooleanField(
        default=True
    )  # True for AI, False for human review
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )  # None for AI, User for human

    history = HistoricalRecords()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["response_annotation", "theme", "is_original_ai_assignment"],
                name="unique_theme_assignment",
            ),
        ]
        indexes = [
            models.Index(fields=["response_annotation", "is_original_ai_assignment"]),
            models.Index(fields=["theme", "is_original_ai_assignment"]),
        ]


class ResponseAnnotation(UUIDPrimaryKeyModel, TimeStampedModel):
    """AI outputs and human reviews for a response"""

    class Sentiment(models.TextChoices):
        AGREEMENT = "AGREEMENT", "Agreement"
        DISAGREEMENT = "DISAGREEMENT", "Disagreement"
        UNCLEAR = "UNCLEAR", "Unclear"

    response = models.OneToOneField(Response, on_delete=models.CASCADE, related_name="annotation")

    # AI-generated outputs (only for free text responses)
    themes = models.ManyToManyField(Theme, through=ResponseAnnotationTheme, blank=True)
    sentiment = models.CharField(max_length=12, choices=Sentiment.choices, null=True, blank=True)
    evidence_rich = models.BooleanField(default=False, null=True, blank=True)

    # Human review tracking
    human_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    flagged_by = models.ManyToManyField(to=User, blank=True, related_name="flagged_by")

    # History tracking
    history = HistoricalRecords()

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
                is_original_ai_assignment=True,
                defaults={"assigned_by": None},
            )

    def set_human_reviewed_themes(self, themes, user):
        """Set themes as human-reviewed, preserving original AI assignments"""
        # Remove existing human-reviewed theme assignments
        ResponseAnnotationTheme.objects.filter(
            response_annotation=self, is_original_ai_assignment=False
        ).delete()

        # Add new human-reviewed theme assignments
        for theme in themes:
            ResponseAnnotationTheme.objects.get_or_create(
                response_annotation=self,
                theme=theme,
                is_original_ai_assignment=False,
                defaults={"assigned_by": user},
            )

    def get_original_ai_themes(self):
        """Get themes that were originally assigned by AI"""
        return self.themes.filter(responseannotationtheme__is_original_ai_assignment=True)

    def get_human_reviewed_themes(self):
        """Get themes that were assigned by human review"""
        return self.themes.filter(responseannotationtheme__is_original_ai_assignment=False)

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
