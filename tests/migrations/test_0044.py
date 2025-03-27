import pytest


@pytest.mark.django_db()
def test_0044_delete_duplicate_theme_mappings(migrator):
    old_state = migrator.apply_initial_migration(
        ("consultations", "0043_convert_jsonfield_data_to_json")
    )
    # Set-up old models
    Consultation = old_state.apps.get_model("consultations", "Consultation")
    Question = old_state.apps.get_model("consultations", "Question")
    QuestionPart = old_state.apps.get_model("consultations", "QuestionPart")
    Answer = old_state.apps.get_model("consultations", "Answer")
    Theme = old_state.apps.get_model("consultations", "Theme")
    ThemeMapping = old_state.apps.get_model("consultations", "ThemeMapping")
    Respondent = old_state.apps.get_model("consultations", "Respondent")
    Framework = old_state.apps.get_model("consultations", "Framework")
    ExecutionRun = old_state.apps.get_model("consultations", "ExecutionRun")

    # Set-up example consultation
    consultation = Consultation.objects.create(title="Consultation")
    respondent = Respondent.objects.create(consultation=consultation)
    execution_run = ExecutionRun.objects.create(type="theme_mapping")
    question = Question.objects.create(consultation=consultation)
    qp = QuestionPart.objects.create(type="free_text", question=question)
    framework = Framework.objects.create(execution_run=execution_run, question_part=qp)
    answer1 = Answer.objects.create(question_part=qp, respondent=respondent)
    answer2 = Answer.objects.create(question_part=qp, respondent=respondent)
    theme1 = Theme.objects.create(name="Theme 1", framework=framework)
    theme2 = Theme.objects.create(name="Theme 2", framework=framework)

    # Set-up theme mappings with some duplicates
    tm1 = ThemeMapping.objects.create(answer=answer1, theme=theme1)
    duplicate0 = ThemeMapping.objects.create(answer=answer1, theme=theme2)
    duplicate1 = ThemeMapping.objects.create(answer=answer1, theme=theme2)
    duplicate2 = ThemeMapping.objects.create(answer=answer1, theme=theme2)
    tm2 = ThemeMapping.objects.create(answer=answer2, theme=theme1)

    # Run migration
    new_state = migrator.apply_tested_migration(
        ("consultations", "0044_delete_duplicate_theme_mappings")
    )

    ThemeMapping = new_state.apps.get_model("consultations", "ThemeMapping")

    # Check that non-duplicates, and the first duplicate, are kept
    # Delete subsequent duplicates
    assert ThemeMapping.objects.count() == 3
    assert ThemeMapping.objects.filter(id=tm1.id).exists()
    assert ThemeMapping.objects.filter(id=duplicate0.id).exists()
    assert ThemeMapping.objects.filter(id=tm2.id).exists()
    assert not ThemeMapping.objects.filter(id=duplicate1.id).exists()
    assert not ThemeMapping.objects.filter(id=duplicate2.id).exists()

    # Cleanup:
    migrator.reset()
