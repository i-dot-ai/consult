import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models

# TODO - Redo these tests with updated fixtures

# def set_up_frameworks():
#     user_1 = factories.UserFactory()
#     user_2 = factories.UserFactory()
#     question_part = factories.QuestionPartFactory(type=models.QuestionPart.QuestionType.FREE_TEXT)

#     # Set up initial framework - replicate a run of the theme generation task.
#     theme_generation_run = factories.ExecutionRunFactory(
#         type=models.ExecutionRun.TaskType.THEME_GENERATION
#     )
#     framework_1 = factories.InitialFrameworkFactory(
#         execution_run=theme_generation_run, question_part=question_part
#     )
#     theme_x = factories.ThemeFactory(name="X", framework=framework_1)
#     theme_y = factories.ThemeFactory(name="Y", framework=framework_1)
#     factories.ThemeFactory(name="Z", framework=framework_1)

#     # Create a new framework amending these themes
#     framework_2a = framework_1.amend_framework(
#         user=user_1, change_reason="I wanted to change the themes."
#     )
#     factories.ThemeFactory(name="X2", framework=framework_2a, precursor=theme_x)

#     # Create another new framework amending the initial themes
#     framework_2b = framework_1.amend_framework(
#         user=user_2, change_reason="I wanted to change the themes in a different way."
#     )
#     factories.ThemeFactory(name="Y2", framework=framework_2b, precursor=theme_y)
#     factories.ThemeFactory(name="W", framework=framework_2b, precursor=None)

#     return framework_1, framework_2a, framework_2b


# @pytest.mark.django_db
# def test_amend_framework():
#     framework_1, _, _ = set_up_frameworks()
#     user = factories.UserFactory()
#     amended_framework = framework_1.amend_framework(
#         user=user, change_reason="I wanted to change the themes."
#     )
#     # ID, precursor, user, change reason should all be updated.
#     assert amended_framework.id != framework_1.id
#     assert amended_framework.precursor == framework_1
#     assert amended_framework.user == user
#     assert amended_framework.change_reason == "I wanted to change the themes."
#     # Question part should be the same
#     assert amended_framework.question_part == framework_1.question_part


@pytest.mark.django_db
def test_cant_save():
    framework = models.Framework()
    with pytest.raises(ValueError):
        framework.save()


@pytest.mark.django_db
def test_create_initial_framework():
    with pytest.raises(ValueError):
        models.Framework.create_inital_framework(
            execution_run=None, question_part=factories.QuestionPartFactory()
        )

    execution_run = factories.ExecutionRunFactory()
    question_part = factories.QuestionPartFactory()
    framework = models.Framework.create_inital_framework(
        execution_run=execution_run, question_part=question_part
    )
    assert framework.id
    assert not framework.precursor
    assert not framework.user
    assert not framework.change_reason
    assert framework.execution_run == execution_run
    assert framework.question_part == question_part


# @pytest.mark.django_db
# def test_get_themes_removed_from_previous_framework():
#     framework_1, framework_2a, framework_2b = set_up_frameworks()
#     removed_themes = framework_1.get_themes_removed_from_previous_framework()
#     assert len(removed_themes) == 0

#     removed_themes = framework_2a.get_themes_removed_from_previous_framework()
#     theme_y = models.Theme.objects.get(name="Y")
#     assert len(removed_themes) == 2
#     assert theme_y in removed_themes
#     assert removed_themes[0].name == "Y"

#     removed_themes = framework_2b.get_themes_removed_from_previous_framework()
#     assert len(removed_themes) == 2
#     assert set(removed_themes.values_list("name", flat=True)) == {"X", "Z"}


# @pytest.mark.django_db
# def test_get_themes_added_from_previous_framework():
#     framework_1, framework_2a, framework_2b = set_up_frameworks()
#     theme_x = models.Theme.objects.get(name="X")
#     theme_w = models.Theme.objects.get(name="W")

#     themes = framework_1.get_themes_added_to_previous_framework()
#     assert len(themes) == 3
#     assert theme_x in themes

#     themes = framework_2a.get_themes_added_to_previous_framework()
#     assert len(themes) == 0

#     themes = framework_2b.get_themes_added_to_previous_framework()
#     assert len(themes) == 1
#     assert theme_w in themes