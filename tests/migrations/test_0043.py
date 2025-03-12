import pytest


@pytest.mark.django_db()
def test_0043_convert_jsonfield_data_to_json(migrator):
    old_state = migrator.apply_initial_migration(
        ("consultations", "0042_respondent_themefinder_respondent_id")
    )

    Consultation = old_state.apps.get_model("consultations", "Consultation")
    Question = old_state.apps.get_model("consultations", "Question")
    QuestionPart = old_state.apps.get_model("consultations", "QuestionPart")
    Respondent = old_state.apps.get_model("consultations", "Respondent")
    Answer = old_state.apps.get_model("consultations", "Answer")

    consultation = Consultation.objects.create(title="Consultation")
    question = Question.objects.create(consultation=consultation)
    qp = QuestionPart.objects.create(options='["option1", "option2"]', question=question)
    respondent = Respondent.objects.create(data='{"key": "value"}', consultation=consultation)
    answer_1 = Answer.objects.create(
        chosen_options='["option1", "option2"]', question_part=qp, respondent=respondent
    )
    answer_2 = Answer.objects.create(
        chosen_options="option1", question_part=qp, respondent=respondent
    )

    new_state = migrator.apply_tested_migration(
        ("consultations", "0043_convert_jsonfield_data_to_json")
    )

    QuestionPart = new_state.apps.get_model("consultations", "QuestionPart")
    Respondent = new_state.apps.get_model("consultations", "Respondent")
    Answer = new_state.apps.get_model("consultations", "Answer")

    qp = QuestionPart.objects.get(pk=qp.pk)
    respondent = Respondent.objects.get(pk=respondent.pk)
    answer_1 = Answer.objects.get(pk=answer_1.pk)
    answer_2 = Answer.objects.get(pk=answer_2.pk)

    assert qp.options == ["option1", "option2"]
    assert type(qp.options) is list
    assert respondent.data == {"key": "value"}
    assert type(respondent.data) is dict
    assert answer_1.chosen_options == ["option1", "option2"]
    assert type(answer_1.chosen_options) is list
    assert answer_2.chosen_options == ["option1"]
    assert type(answer_2.chosen_options) is list

    # Cleanup:
    migrator.reset()
