import pytest

from consultation_analyser.consultations.models import Theme
from consultation_analyser.factories import (
    DescendantFrameworkFactory,
    FreeTextQuestionPartFactory,
    InitialFrameworkFactory,
    InitialThemeFactory,
)


@pytest.mark.django_db
def test_cant_use_save():
    theme = InitialThemeFactory()
    with pytest.raises(ValueError) as excinfo:
        theme.save()
    assert "Direct save() method is not allowed" in str(excinfo.value)


@pytest.mark.django_db
def test_create_initial_theme():
    framework = InitialFrameworkFactory()
    name = "Test Theme"
    description = "Test Description"
    new_theme = Theme.create_initial_theme(framework=framework, name=name, description=description)
    assert new_theme.framework == framework
    assert not new_theme.precursor


@pytest.mark.django_db
def test_create_descendant_theme():
    question_part = FreeTextQuestionPartFactory()
    initial_framework = InitialFrameworkFactory(question_part=question_part)
    initial_theme = InitialThemeFactory(framework=initial_framework)
    descendant_framework = DescendantFrameworkFactory(precursor=initial_framework)
    random_framework = InitialFrameworkFactory(question_part=question_part)

    # The descendant theme must be based on a descendant framework
    with pytest.raises(ValueError) as excinfo:
        initial_theme.create_descendant_theme(
            name="name", description="description", new_framework=random_framework
        )
    assert "Framework for new theme must be based on the framework for the existing theme." in str(
        excinfo.value
    )

    new_theme = initial_theme.create_descendant_theme(
        new_framework=descendant_framework, name="name", description="description"
    )
    assert new_theme.framework == descendant_framework
    assert new_theme.precursor == initial_theme
    assert new_theme.name == "name"
    assert new_theme.description == "description"
