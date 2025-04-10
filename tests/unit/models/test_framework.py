import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import (
    ExecutionRun,
    Framework,
    ThemeMapping,
)


@pytest.mark.django_db
def test_cant_save():
    framework = Framework()
    with pytest.raises(ValueError):
        framework.save()


@pytest.mark.django_db
def test_create_initial_framework():
    question_part = factories.FreeTextQuestionPartFactory()
    with pytest.raises(ValueError):
        Framework.create_initial_framework(
            theme_generation_execution_run=None, question_part=question_part
        )
    theme_mapping_execution_run = factories.ExecutionRunFactory(
        type=ExecutionRun.TaskType.THEME_MAPPING
    )
    theme_generation_execution_run = factories.ExecutionRunFactory(
        type=ExecutionRun.TaskType.THEME_GENERATION
    )
    with pytest.raises(ValueError):
        Framework.create_initial_framework(
            theme_generation_execution_run=theme_mapping_execution_run, question_part=question_part
        )

    framework = Framework.create_initial_framework(
        theme_generation_execution_run=theme_generation_execution_run, question_part=question_part
    )
    assert framework.id
    assert not framework.precursor
    assert not framework.user
    assert not framework.change_reason
    assert framework.theme_generation_execution_run == theme_generation_execution_run
    assert framework.question_part == question_part


@pytest.mark.django_db
def test_create_descendant_framework():
    initial_framework = factories.InitialFrameworkFactory()
    user = factories.UserFactory()
    new_framework = initial_framework.create_descendant_framework(
        user=user, change_reason="I wanted to change the themes."
    )
    assert new_framework.id
    assert Framework.objects.filter(id=new_framework.id).exists()
    assert new_framework.question_part == initial_framework.question_part
    assert new_framework.id != initial_framework.id
    assert new_framework.precursor == initial_framework
    assert new_framework.user == user
    assert new_framework.change_reason == "I wanted to change the themes."
    assert not new_framework.theme_generation_execution_run


@pytest.mark.django_db
def test_get_themes_removed_from_previous_framework():
    # Create framework with 3 themes
    initial_theme_1 = factories.InitialThemeFactory(name="initial_theme_1", key="A")
    initial_framework = initial_theme_1.framework
    initial_theme_2 = factories.InitialThemeFactory(
        name="initial_theme_2", framework=initial_framework, key="B"
    )
    initial_theme_3 = factories.InitialThemeFactory(
        name="initial_theme_3", framework=initial_framework, key="C"
    )

    # Create subsequent framework, one theme persists
    descendent_framework = initial_framework.create_descendant_framework(
        user=factories.UserFactory(), change_reason="I wanted to change the themes."
    )
    initial_theme_1.create_descendant_theme(
        new_framework=descendent_framework, name="descendant theme", description="descendant theme"
    )
    themes_removed = descendent_framework.get_themes_removed_from_previous_framework()
    assert len(themes_removed) == 2
    assert initial_theme_2 in themes_removed
    assert initial_theme_3 in themes_removed
    assert initial_theme_1 not in themes_removed


@pytest.mark.django_db
def test_get_theme_mappings():
    # Set up questions and answers
    question_part = factories.FreeTextQuestionPartFactory()
    answer_1 = factories.FreeTextAnswerFactory(question_part=question_part)
    answer_2 = factories.FreeTextAnswerFactory(question_part=question_part)
    answer_3 = factories.FreeTextAnswerFactory(question_part=question_part)

    # First framework and mappings
    framework1 = factories.InitialFrameworkFactory(question_part=question_part)
    theme1 = factories.InitialThemeFactory(framework=framework1)
    ThemeMapping.objects.create(theme=theme1, answer=answer_1)

    # Latest framework and mappings - make sure there are some historical themes.
    framework2 = factories.InitialFrameworkFactory(question_part=question_part)
    theme_a = factories.InitialThemeFactory(framework=framework2)
    theme_b = factories.InitialThemeFactory(framework=framework2)
    theme_c = factories.InitialThemeFactory(framework=framework2)
    tm1 = ThemeMapping.objects.create(answer=answer_1, theme=theme_a)
    tm2 = ThemeMapping.objects.create(answer=answer_1, theme=theme_b)
    ThemeMapping.objects.create(answer=answer_2, theme=theme_b)
    ThemeMapping.objects.create(answer=answer_3, theme=theme_c)
    tm2.delete()

    # Check get_theme_mappings
    latest_qs = framework2.get_theme_mappings()
    assert latest_qs.count() == 3
    assert tm1 in latest_qs
    assert tm2 not in latest_qs

    # Check with history
    theme_mappings_with_history = framework2.get_theme_mappings(history=True)
    assert theme_mappings_with_history.count() == 5
    mapping = theme_mappings_with_history.get(theme=theme_a, answer=answer_1)
    assert mapping.history_type == "+"
    mappings = theme_mappings_with_history.filter(theme=theme_b, answer=answer_1)
    assert mappings.count() == 2
    assert mappings.latest().history_type == "-"
