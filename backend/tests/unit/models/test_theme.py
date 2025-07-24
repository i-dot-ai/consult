import pytest
from django.db.utils import IntegrityError

from consultation_analyser.consultations.models import Theme
from consultation_analyser.factories import (
    QuestionFactory,
    ThemeFactory,
)


@pytest.mark.django_db
class TestTheme:
    def test_theme_creation(self):
        """Test basic theme creation"""
        theme = ThemeFactory()
        assert isinstance(theme, Theme)
        assert theme.name
        assert theme.description
        assert theme.key
        assert theme.question

    def test_theme_str_representation(self):
        """Test string representation of theme"""
        theme = ThemeFactory(name="Environmental Impact")
        assert str(theme) == "Environmental Impact"

    def test_theme_key_uniqueness_per_question(self):
        """Test that theme keys must be unique within a question"""
        question = QuestionFactory()
        ThemeFactory(question=question, key="ENV")

        # Can't create another theme with same key for same question
        with pytest.raises(IntegrityError):
            Theme.objects.create(
                question=question,
                name="Another Environmental Theme",
                description="Different description",
                key="ENV",
            )

    def test_theme_key_can_be_reused_across_questions(self):
        """Test that same key can be used for themes in different questions"""
        question1 = QuestionFactory()
        question2 = QuestionFactory()

        theme1 = ThemeFactory(question=question1, key="ENV")
        theme2 = ThemeFactory(question=question2, key="ENV")

        assert theme1.key == theme2.key
        assert theme1.question != theme2.question

    def test_theme_without_key(self):
        """Test that themes can be created without a key"""
        theme1 = ThemeFactory(key=None)
        theme2 = ThemeFactory(key=None, question=theme1.question)

        # Both themes can exist without keys even for same question
        assert theme1.key is None
        assert theme2.key is None
        assert theme1.question == theme2.question

    def test_theme_question_relationship(self):
        """Test the foreign key relationship with Question"""
        question = QuestionFactory()
        theme1 = ThemeFactory(question=question)
        theme2 = ThemeFactory(question=question)

        # Check reverse relationship
        question_themes = question.theme_set.all()
        assert theme1 in question_themes
        assert theme2 in question_themes
        assert question_themes.count() == 2
