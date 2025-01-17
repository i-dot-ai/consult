import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_cant_save():
    framework = models.Framework()
    with pytest.raises(ValueError):
        framework.save()


@pytest.mark.django_db
def test_create_initial_framework():
    with pytest.raises(ValueError):
        models.Framework.create_initial_framework(
            execution_run=None, question_part=factories.FreeTextQuestionPartFactory()
        )
    execution_run = factories.ExecutionRunFactory()
    question_part = factories.FreeTextQuestionPartFactory()
    framework = models.Framework.create_initial_framework(
        execution_run=execution_run, question_part=question_part
    )
    assert framework.id
    assert not framework.precursor
    assert not framework.user
    assert not framework.change_reason
    assert framework.execution_run == execution_run
    assert framework.question_part == question_part


@pytest.mark.django_db
def test_create_descendant_framework():
    initial_framework = factories.InitialFrameworkFactory()
    user = factories.UserFactory()
    new_framework = initial_framework.create_descendant_framework(
        user=user, change_reason="I wanted to change the themes."
    )
    assert new_framework.id
    assert models.Framework.objects.filter(id=new_framework.id).exists()
    assert new_framework.question_part == initial_framework.question_part
    assert new_framework.id != initial_framework.id
    assert new_framework.precursor == initial_framework
    assert new_framework.user == user
    assert new_framework.change_reason == "I wanted to change the themes."
    assert not new_framework.execution_run


@pytest.mark.django_db
def test_get_themes_removed_from_previous_framework():
    # Create framework with 3 themes
    initial_theme_1 = factories.InitialThemeFactory(name="initial_theme_1")
    initial_framework = initial_theme_1.framework
    initial_theme_2 = factories.InitialThemeFactory(
        name="initial_theme_2", framework=initial_framework
    )
    initial_theme_3 = factories.InitialThemeFactory(
        name="initial_theme_3", framework=initial_framework
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
