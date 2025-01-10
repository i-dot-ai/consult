# TODO - need to fix these objects

# def set_up_frameworks():
#     question_part = factories.QuestionPartFactory(type=models.QuestionPart.QuestionType.FREE_TEXT)

#     # Set up initial framework - replicate a run of the theme generation task.
#     theme_generation_run = factories.ExecutionRunFactory(
#         type=models.ExecutionRun.TaskType.THEME_GENERATION
#     )
#     framework_1 = factories.InitialFrameworkFactory(
#         execution_run=theme_generation_run, question_part=question_part
#     )
#     factories.InitialThemeFactory(name="X", framework=framework_1)
#     factories.InitialThemeFactory(name="Y", framework=framework_1)
#     factories.InitialThemeFactory(name="Z", framework=framework_1)

#     # Create a new framework amending these themes
#     framework_2 = framework_1.amend_framework(
#         user=factories.UserFactory(), change_reason="I wanted to change the themes."
#     )
#     return framework_1, framework_2


# @pytest.mark.django_db
# def test_amend_theme():
#     framework_1, framework_2 = set_up_frameworks()
#     theme_x = models.Theme.objects.get(name="X", framework=framework_1)
#     models.Theme.objects.get(name="Y", framework=framework_1)

#     with pytest.raises(ValueError):
#         theme_x.amend_theme(
#             new_framework=factories.InitialFrameworkFactory(),
#             name="change X",
#             description="longer description",
#         )

#     updated_x = theme_x.amend_theme(
#         new_framework=framework_2, name="change X", description="longer description"
#     )
#     assert updated_x.id != theme_x.id
#     assert updated_x.name == "change X"
#     assert updated_x.description == "longer description"
#     assert updated_x.framework == framework_2
#     assert updated_x.precursor == theme_x
