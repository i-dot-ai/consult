import pytest
from django.db.utils import IntegrityError

from consultation_analyser.consultations.models import SelectedTheme
from consultation_analyser.factories import (
    QuestionFactory,
    SelectedThemeFactory,
)


@pytest.mark.django_db
class TestTheme:
    def test_theme_creation(self):
        """Test basic theme creation"""
        theme = SelectedThemeFactory()
        assert isinstance(theme, SelectedTheme)
        assert theme.name
        assert theme.description
        assert theme.key
        assert theme.question

    def test_theme_str_representation(self):
        """Test string representation of theme"""
        theme = SelectedThemeFactory(name="Environmental Impact")
        assert str(theme) == "Environmental Impact"

    def test_theme_key_uniqueness_per_question(self):
        """Test that theme keys must be unique within a question"""
        theme = SelectedThemeFactory(key="ENV")

        # Can't create another theme with same key for same question
        with pytest.raises(IntegrityError):
            SelectedTheme.objects.create(
                question=theme.question,
                name="Another Environmental Theme",
                description="Different description",
                key=theme.key,
            )

    def test_theme_key_can_be_reused_across_questions(self, free_text_question):
        """Test that same key can be used for themes in different questions"""
        question2 = QuestionFactory()

        theme1 = SelectedThemeFactory(question=free_text_question, key="ENV")
        theme2 = SelectedThemeFactory(question=question2, key="ENV")

        assert theme1.key == theme2.key
        assert theme1.question != theme2.question

    def test_theme_without_key(self):
        """Test that themes can be created without a key"""
        theme1 = SelectedThemeFactory(key=None)
        theme2 = SelectedThemeFactory(key=None, question=theme1.question)

        # Both themes can exist without keys even for same question
        assert theme1.key is None
        assert theme2.key is None
        assert theme1.question == theme2.question

    def test_theme_question_relationship(self, free_text_question):
        """Test the foreign key relationship with Question"""
        theme1 = SelectedThemeFactory(question=free_text_question)
        theme2 = SelectedThemeFactory(question=free_text_question)

        # Check reverse relationship
        question_themes = free_text_question.selectedtheme_set.all()
        assert theme1 in question_themes
        assert theme2 in question_themes
        assert question_themes.count() == 2
