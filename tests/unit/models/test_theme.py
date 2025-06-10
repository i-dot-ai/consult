import pytest
from django.db.utils import IntegrityError

from consultation_analyser.consultations.models import ThemeOld
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
    new_theme = ThemeOld.create_initial_theme(framework=framework, name=name, description=description)
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


@pytest.mark.django_db
def test_get_theme_identifier():
    framework = InitialFrameworkFactory()
    theme_1 = ThemeOld.create_initial_theme(
        framework=framework, name="Theme 1", description=""
    )  # no key
    theme_2 = ThemeOld.create_initial_theme(
        framework=framework, name="Theme 2", description="", key="A"
    )  # with key

    assert theme_1.get_identifier() == "Theme 1"
    assert theme_2.get_identifier() == "A"


@pytest.mark.django_db
def test_theme_key_uniqueness():
    framework = InitialFrameworkFactory()
    ThemeOld.create_initial_theme(framework=framework, name="Theme 1", description="", key="A")

    # Can have two themes with the same key in different frameworks
    framework_2 = InitialFrameworkFactory()
    ThemeOld.create_initial_theme(framework=framework_2, name="Theme 1", description="", key="A")

    # Cannot have two themes in the same framework with the same key
    with pytest.raises(IntegrityError):
        ThemeOld.create_initial_theme(framework=framework, name="Theme 1", description="", key="A")
