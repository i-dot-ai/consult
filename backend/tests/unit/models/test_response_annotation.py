import pytest
from backend.factories import (
    ResponseAnnotationFactory,
    ResponseFactory,
    ReviewedResponseAnnotationFactory,
    SelectedThemeFactory,
    UserFactory,
)
from django.utils import timezone
from freezegun import freeze_time

from backend.consultations.models import Response


@pytest.mark.django_db
class TestResponseAnnotation:
    def test_annotation_creation(self):
        """Test basic annotation creation"""
        annotation = ResponseAnnotationFactory()
        assert isinstance(annotation, Response)
        assert annotation.sentiment in ["AGREEMENT", "DISAGREEMENT", "UNCLEAR"]
        assert isinstance(annotation.evidence_rich, bool)
        assert not annotation.human_reviewed
        assert annotation.reviewed_by is None
        assert annotation.reviewed_at is None


    def test_themes_relationship(self):
        """Test many-to-many relationship with themes"""
        response = ResponseAnnotationFactory()

        # Should have auto-created themes
        assert response.themes.count() >= 1

        # All themes should be for the same question as the response
        for theme in response.themes.all():
            assert theme.question == response.question

    def test_custom_themes(self):
        """Test creating annotation with specific themes"""
        response = ResponseFactory()
        theme1 = SelectedThemeFactory(question=response.question)
        theme2 = SelectedThemeFactory(question=response.question)
        response.add_original_ai_themes([theme1, theme2])

        assert response.themes.count() == 2
        assert theme1 in response.themes.all()
        assert theme2 in response.themes.all()



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

