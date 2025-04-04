import django
import pytest

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    FreeTextAnswerFactory,
    FreeTextQuestionPartFactory,
    InitialFrameworkFactory,
    InitialThemeFactory,
    ThemeMappingFactory,
)


@pytest.mark.django_db
def test_get_history_of_theme_mappings_for_answer():
    question_part = FreeTextQuestionPartFactory()
    answer1 = FreeTextAnswerFactory(question_part=question_part)
    framework = InitialFrameworkFactory(question_part=question_part)
    theme1 = InitialThemeFactory(framework=framework, name="theme 1", key="A")
    theme2 = InitialThemeFactory(framework=framework, name="theme 2", key="B")
    theme3 = InitialThemeFactory(framework=framework, name="theme 3", key="C")

    # Now map a theme to the Answer
    theme_mapping = ThemeMappingFactory(
        answer=answer1, theme=theme1, reason="Theme 1 is most reasonable"
    )

    # Now change the theme mapping
    theme_mapping.theme = theme2
    theme_mapping.save()
    theme_mapping.theme = theme3
    theme_mapping.save()

    # Check current status i.e. latest theme mapping
    assert theme_mapping.theme == theme3


@pytest.mark.django_db
def test_get_latest_theme_mappings():
    question_part = FreeTextQuestionPartFactory()
    answer = FreeTextAnswerFactory(question_part=question_part)
    answer2 = FreeTextAnswerFactory(question_part=question_part)

    framework1 = InitialFrameworkFactory(question_part=question_part)
    framework2 = InitialFrameworkFactory(question_part=question_part)
    InitialFrameworkFactory()  # random framework - diff question

    # Return empty querysets as no theme mappings yet
    qs = framework1.get_theme_mappings()
    assert not qs.count()
    qs = framework1.get_theme_mappings(history=True)
    assert not qs.count()

    # Now add some mappings including some historical mappings
    # Framework 1 themes
    theme = InitialThemeFactory(framework=framework1, key="A")
    theme2 = InitialThemeFactory(framework=framework1, key="B")

    # Framework 2 themes
    theme3 = InitialThemeFactory(framework=framework2, key="C")
    theme4 = InitialThemeFactory(framework=framework2, key="D")

    # Theme mappings for framework 1
    ThemeMappingFactory(answer=answer, theme=theme)
    ThemeMappingFactory(answer=answer2, theme=theme2)

    # Theme mappings for framework 2
    mapping1 = ThemeMappingFactory(answer=answer, theme=theme3)
    ThemeMappingFactory(answer=answer2, theme=theme4)
    ThemeMappingFactory(answer=answer2, theme=theme3)
    mapping1.delete()

    theme_mappings_qs = models.ThemeMapping.get_latest_theme_mappings(
        question_part=question_part, history=False
    )
    assert theme_mappings_qs.count() == 2
    assert theme_mappings_qs.first().theme.framework == framework2

    historical_theme_mappings_qs = models.ThemeMapping.get_latest_theme_mappings(
        question_part=question_part, history=True
    )
    assert historical_theme_mappings_qs.count() == 4
    assert historical_theme_mappings_qs.first().theme.framework == framework2
    changed_mapping = historical_theme_mappings_qs.filter(answer=answer, theme=theme3)
    assert changed_mapping.count() == 2
    assert set(changed_mapping.values_list("history_type", flat=True)) == set(["-", "+"])


@pytest.mark.django_db
def test_check_uniqueness():
    theme_mapping = ThemeMappingFactory()
    answer = theme_mapping.answer
    theme = theme_mapping.theme

    # Create a duplicate theme mapping
    duplicate = models.ThemeMapping(answer=answer, theme=theme)
    with pytest.raises(django.db.utils.IntegrityError):
        duplicate.save()
