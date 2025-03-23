import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import ExecutionRun, Framework


@pytest.mark.django_db
def test_cant_save():
    framework = Framework()
    with pytest.raises(ValueError):
        framework.save()


@pytest.mark.django_db
def test_create_initial_framework():
    question_part = factories.FreeTextQuestionPartFactory()
    with pytest.raises(ValueError):
        Framework.create_initial_framework(execution_run=None, question_part=question_part)
    theme_mapping_execution_run = factories.ExecutionRunFactory(
        type=ExecutionRun.TaskType.THEME_MAPPING
    )
    theme_generation_execution_run = factories.ExecutionRunFactory(
        type=ExecutionRun.TaskType.THEME_GENERATION
    )
    with pytest.raises(ValueError):
        Framework.create_initial_framework(
            execution_run=theme_mapping_execution_run, question_part=question_part
        )

    framework = Framework.create_initial_framework(
        execution_run=theme_generation_execution_run, question_part=question_part
    )
    assert framework.id
    assert not framework.precursor
    assert not framework.user
    assert not framework.change_reason
    assert framework.execution_run == theme_generation_execution_run
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
    assert not new_framework.execution_run


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
    theme = factories.InitialThemeFactory()
    framework = theme.framework
    # No theme mappings
    qs = framework.get_theme_mappings()
    assert qs.count() == 0

    # Now add some theme mappings
    question_part = framework.question_part
    theme2 = factories.InitialThemeFactory(framework=framework)
    answer = factories.FreeTextAnswerFactory(question_part=question_part)
    answer2 = factories.FreeTextAnswerFactory(question_part=question_part)
    diff_answer = factories.FreeTextAnswerFactory()
    theme_mapping = factories.ThemeMappingFactory(answer=answer, theme=theme)
    factories.ThemeMappingFactory(answer=answer, theme=theme2)
    factories.ThemeMappingFactory(answer=answer2, theme=theme2)
    diff_theme_mapping = factories.ThemeMappingFactory(answer=diff_answer)

    qs = framework.get_theme_mappings()
    assert qs.count() == 3
    assert theme_mapping in qs
    assert diff_theme_mapping not in qs


@pytest.mark.django_db
def test_get_latest_theme_mappings():
    question_part = factories.FreeTextQuestionPartFactory()
    answer = factories.FreeTextAnswerFactory(question_part=question_part)
    answer2 = factories.FreeTextAnswerFactory(question_part=question_part)

    framework1 = factories.InitialFrameworkFactory(question_part=question_part)
    framework2 = factories.InitialFrameworkFactory(question_part=question_part)
    factories.InitialFrameworkFactory()  # random framework - diff question

    # Framework 1 themes
    theme = factories.InitialThemeFactory(framework=framework1)
    theme2 = factories.InitialThemeFactory(framework=framework1)

    # Framework 2 themes
    theme3 = factories.InitialThemeFactory(framework=framework2)
    theme4 = factories.InitialThemeFactory(framework=framework2)

    # Theme mappings for framework 1
    factories.ThemeMappingFactory(answer=answer, theme=theme)
    factories.ThemeMappingFactory(answer=answer2, theme=theme2)

    # Theme mappings for framework 2
    factories.ThemeMappingFactory(answer=answer, theme=theme3)
    factories.ThemeMappingFactory(answer=answer2, theme=theme4)
    factories.ThemeMappingFactory(answer=answer2, theme=theme3)

    theme_mappings_qs = Framework.get_latest_theme_mappings(question_part=question_part)
    assert theme_mappings_qs.count() == 3
    assert theme_mappings_qs.first().theme.framework == framework2
