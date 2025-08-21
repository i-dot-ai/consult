import pytest
from django.utils import timezone
from freezegun import freeze_time

from consultation_analyser.consultations.models import ResponseAnnotation
from consultation_analyser.factories import (
    ResponseAnnotationFactory,
    ResponseFactory,
    ReviewedResponseAnnotationFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestResponseAnnotation:
    def test_annotation_creation(self):
        """Test basic annotation creation"""
        annotation = ResponseAnnotationFactory()
        assert isinstance(annotation, ResponseAnnotation)
        assert annotation.sentiment in ["AGREEMENT", "DISAGREEMENT", "UNCLEAR"]
        assert isinstance(annotation.evidence_rich, bool)
        assert not annotation.human_reviewed
        assert annotation.reviewed_by is None
        assert annotation.reviewed_at is None

    def test_one_to_one_relationship(self):
        """Test one-to-one relationship with Response"""
        response = ResponseFactory()
        annotation = ResponseAnnotationFactory(response=response)

        # Check bidirectional relationship
        assert response.annotation == annotation
        assert annotation.response == response

        # Can't create another annotation for same response
        with pytest.raises(Exception):  # Will raise IntegrityError
            ResponseAnnotationFactory(response=response)

    def test_themes_relationship(self):
        """Test many-to-many relationship with themes"""
        annotation = ResponseAnnotationFactory()

        # Should have auto-created themes
        assert annotation.themes.count() >= 1

        # All themes should be for the same question as the response
        for theme in annotation.themes.all():
            assert theme.question == annotation.response.question

    def test_custom_themes(self, response_1, theme_a, theme_b):
        """Test creating annotation with specific themes"""

        annotation = ResponseAnnotationFactory(response=response_1, themes=[theme_a, theme_b])

        assert annotation.themes.count() == 2
        assert theme_a in annotation.themes.all()
        assert theme_b in annotation.themes.all()

    def test_sentiment_choices(self, response_1):
        """Test sentiment field choices"""

        # Test each valid choice
        for sentiment in ["AGREEMENT", "DISAGREEMENT", "UNCLEAR"]:
            annotation = ResponseAnnotation.objects.create(response=response_1, sentiment=sentiment)
            assert annotation.sentiment == sentiment
            annotation.delete()

    def test_evidence_rich_choices(self, response_1):
        """Test evidence_rich field choices"""

        # Test each valid choice
        for evidence in [True, False]:
            annotation = ResponseAnnotation.objects.create(
                response=response_1, evidence_rich=evidence
            )
            assert annotation.evidence_rich == evidence
            annotation.delete()

    def test_human_review_tracking(self):
        """Test human review functionality"""
        annotation = ResponseAnnotationFactory()
        user = UserFactory()

        with freeze_time("2024-01-15 10:30:00"):
            annotation.mark_human_reviewed(user)

        assert annotation.human_reviewed
        assert annotation.reviewed_by == user
        assert annotation.reviewed_at == timezone.make_aware(
            timezone.datetime(2024, 1, 15, 10, 30, 0)
        )

    def test_reviewed_annotation_factory(self):
        """Test factory for creating reviewed annotations"""
        reviewed = ReviewedResponseAnnotationFactory()

        assert reviewed.human_reviewed
        assert reviewed.reviewed_by is not None
        assert reviewed.reviewed_at is not None

    def test_annotation_without_ai_fields(self, response_1):
        """Test that AI fields are optional (for non-free-text responses)"""
        annotation = ResponseAnnotation.objects.create(
            response=response_1, sentiment=None, evidence_rich=None
        )

        assert annotation.sentiment is None
        assert annotation.evidence_rich is None
        assert annotation.themes.count() == 0
