import pytest
from django.db.models import F
from django.utils import timezone

from consultations.models import (
    Consultation,
    DemographicOption,
    Question,
    Response,
    ResponseAnnotation,
    SelectedTheme,
)
from consultations.services.migrate_v1_to_v2 import (
    _assign_stage,
    _backfill_question_types,
    _convert_demographics,
    _convert_multiple_choice_to_responses,
    _fill_response_text,
    _refresh_denormalised_counts,
    audit_consultation,
    migrate_consultation_to_v2,
)
from factories import (
    CandidateThemeFactory,
    ConsultationFactory,
    MultiChoiceAnswerFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def v1_consultation():
    consultation = ConsultationFactory(is_v1=True)
    respondent = RespondentFactory(consultation=consultation)

    open_question = QuestionFactory(
        consultation=consultation, has_free_text=True, has_multiple_choice=False
    )
    ResponseFactory(question=open_question, respondent=respondent, free_text="Hello world")

    closed_question = QuestionFactory(
        consultation=consultation, has_free_text=False, has_multiple_choice=True
    )
    closed_response = ResponseFactory(
        question=closed_question, respondent=respondent, free_text=None
    )
    closed_response.chosen_options.add(
        MultiChoiceAnswerFactory(question=closed_question, text="Red"),
        MultiChoiceAnswerFactory(question=closed_question, text="Blue"),
    )

    hybrid_question = QuestionFactory(
        consultation=consultation, has_free_text=True, has_multiple_choice=True
    )
    hybrid_response = ResponseFactory(
        question=hybrid_question, respondent=respondent, free_text="Specify other"
    )
    hybrid_response.chosen_options.add(
        MultiChoiceAnswerFactory(question=hybrid_question, text="Maybe")
    )

    QuestionFactory(consultation=consultation, has_free_text=False, has_multiple_choice=False)
    for field_name, field_value in [("Nation", "England"), ("Age", "18-35")]:
        option = DemographicOption.objects.create(
            consultation=consultation, field_name=field_name, field_value=field_value
        )
        respondent.demographics.add(option)

    return consultation


def test_audit_counts_v1_shaped_data(v1_consultation):
    counts = audit_consultation(v1_consultation)

    assert counts["responses_missing_text"] == 2
    assert counts["questions_without_type"] == 4
    assert counts["questions_open_only"] == 1
    assert counts["questions_closed_only"] == 1
    assert counts["questions_hybrid"] == 1
    assert counts["questions_without_flags"] == 1
    assert counts["multiple_choice_links"] == 3
    assert counts["multi_choice_answers"] == 3
    assert counts["demographic_options"] == 2
    assert counts["respondent_demographic_links"] == 2
    assert counts["missing_data_source"] == 1


def test_audit_is_empty_for_v2_consultation():
    consultation = ConsultationFactory(is_v1=False, data_source=Consultation.DataSource.QUALTRICS)

    assert not any(audit_consultation(consultation).values())


def test_migrate_full_chain_end_to_end(v1_consultation):
    result = migrate_consultation_to_v2(v1_consultation)

    result.refresh_from_db()
    assert result.migrated_at is not None
    assert result.is_v1 is True  # origin is preserved even after migrating
    assert result.data_source == Consultation.DataSource.CITIZEN_SPACE

    counts = audit_consultation(v1_consultation)
    assert counts["responses_missing_text"] == 0
    assert counts["questions_open_only"] == 0
    assert counts["questions_closed_only"] == 0
    assert counts["questions_hybrid"] == 0
    assert counts["questions_without_type"] == 1  # the neither-flag question, report-only
    assert counts["missing_data_source"] == 0
    # kept for v1 consumers (decision: keep all)
    assert counts["multiple_choice_links"] == 3
    assert counts["demographic_options"] == 2

    # idempotent: re-running after completion changes nothing
    second = migrate_consultation_to_v2(result)
    assert second == result
    assert audit_consultation(v1_consultation) == counts

    # stage derived from artifacts (responses exist, no themes): FINDING_THEMES
    result.refresh_from_db()
    assert result.stage == Consultation.Stage.FINDING_THEMES
    # the fixture's neither-flag question keeps the completion rule from
    # firing: the record should invite human attention rather than lie
    assert result.survey_import_status == Consultation.SurveyImportStatus.PENDING_QUESTIONS


def test_stage_assignment_from_artifacts():
    consultation = ConsultationFactory(is_v1=True, stage=Consultation.Stage.SETUP)
    question = QuestionFactory(consultation=consultation)
    response = ResponseFactory(question=question)

    def stage_after_step():
        _assign_stage(Consultation.objects.get(id=consultation.id))
        return Consultation.objects.get(id=consultation.id).stage

    # responses only -> theme finding is the current/next step
    assert stage_after_step() == Consultation.Stage.FINDING_THEMES

    CandidateThemeFactory(question=question)
    assert stage_after_step() == Consultation.Stage.FINALISING_THEMES

    SelectedTheme.objects.create(question=question, key="Theme A")
    assert stage_after_step() == Consultation.Stage.ASSIGNING_THEMES

    ResponseAnnotation.objects.create(response=response, evidence_rich=True)
    assert stage_after_step() == Consultation.Stage.ANALYSIS

    # never moves backwards: a consultation recorded as ANALYSIS with data
    # that only evidences FINDING_THEMES stays put
    consultation.stage = Consultation.Stage.SETUP
    consultation.save(update_fields=["stage"])
    assert stage_after_step() == Consultation.Stage.ANALYSIS


def test_survey_import_status_complete_when_all_typed():
    consultation = ConsultationFactory(is_v1=True)
    QuestionFactory(consultation=consultation, type=Question.QuestionType.OPEN, status="configured")

    migrate_consultation_to_v2(consultation)
    consultation.refresh_from_db()
    assert consultation.survey_import_status == Consultation.SurveyImportStatus.IMPORT_COMPLETE


def test_convert_demographics(v1_consultation):
    _convert_demographics(v1_consultation)

    nation = v1_consultation.question_set.get(
        type=Question.QuestionType.DEMOGRAPHIC, text="Nation"
    )
    age = v1_consultation.question_set.get(type=Question.QuestionType.DEMOGRAPHIC, text="Age")
    assert nation.status == Question.ThemeStatus.CONFIGURED
    assert list(nation.response_set.exclude(text__isnull=True).values_list("text", flat=True)) == [
        "England"
    ]
    assert list(age.response_set.exclude(text__isnull=True).values_list("text", flat=True)) == [
        "18-35"
    ]

    # idempotent: re-running creates nothing new
    total_rows = Response.objects.filter(question__consultation=v1_consultation).count()
    _convert_demographics(v1_consultation)
    assert Response.objects.filter(question__consultation=v1_consultation).count() == total_rows


def test_convert_demographics_value_handling():
    consultation = ConsultationFactory(is_v1=True)
    respondent = RespondentFactory(consultation=consultation)
    for field_name, field_value in [
        ("consented", True),
        ("flag", False),
        ("answer", 42),
        ("blank", ""),
        ("dash", "-"),
        ("placeholder", "Not Provided"),
    ]:
        option = DemographicOption.objects.create(
            consultation=consultation, field_name=field_name, field_value=field_value
        )
        respondent.demographics.add(option)

    _convert_demographics(consultation)

    created = dict(
        Response.objects.filter(question__consultation=consultation).values_list(
            "question__text", "text"
        )
    )
    assert created == {"consented": "true", "flag": "false", "answer": "42"}

    # the blank placeholder questions still exist in v2 form but carry no
    # response rows (docstring contract: blank placeholders produce no rows)
    for blank_field in ("blank", "dash", "placeholder"):
        question = consultation.question_set.get(text=blank_field)
        assert question.type == Question.QuestionType.DEMOGRAPHIC
        assert not question.response_set.exists()


def test_migrate_skips_already_migrated_consultations(v1_consultation):
    migrated_at = timezone.now()
    v1_consultation.migrated_at = migrated_at
    v1_consultation.save()
    counts = audit_consultation(v1_consultation)

    result = migrate_consultation_to_v2(v1_consultation)

    assert result.id == v1_consultation.id
    assert result.migrated_at == migrated_at
    assert audit_consultation(v1_consultation) == counts


def test_migrate_marks_consultations_with_survey_provider_as_v2():
    consultation = ConsultationFactory(
        is_v1=True, data_source=Consultation.DataSource.CITIZEN_SPACE
    )
    counts = audit_consultation(consultation)

    result = migrate_consultation_to_v2(consultation)

    assert result.id == consultation.id
    result.refresh_from_db()
    assert result.is_v1 is False
    assert result.migrated_at is None
    assert audit_consultation(consultation) == counts


def test_migrate_marks_consultations_without_survey_provider_as_v1():
    consultation = ConsultationFactory(is_v1=False, data_source=None)

    result = migrate_consultation_to_v2(consultation)

    result.refresh_from_db()
    # classification runs on every attempt until migrated: with no provider
    # set the consultation is V1, so it receives the full migration
    assert result.is_v1 is True
    assert result.migrated_at is not None


def test_refresh_denormalised_counts(v1_consultation):
    _backfill_question_types(v1_consultation)
    _convert_multiple_choice_to_responses(v1_consultation)

    closed_question = next(
        q
        for q in v1_consultation.question_set.all()
        if q.type == Question.QuestionType.CLOSED
        and {a.text for a in q.multichoiceanswer_set.all()} == {"Red", "Blue"}
    )
    open_question = next(
        q
        for q in v1_consultation.question_set.all()
        if q.type == Question.QuestionType.OPEN and q.closed_question_id is None
    )
    hybrid_original = next(
        q
        for q in v1_consultation.question_set.all()
        if q.type == Question.QuestionType.OPEN and q.closed_question_id is not None
    )
    hybrid_sibling = hybrid_original.closed_question
    assert hybrid_sibling.total_response_count == 0  # zeroed until the refresh runs

    _refresh_denormalised_counts(v1_consultation)

    closed_question.refresh_from_db()
    assert (closed_question.total_response_count, closed_question.free_text_response_count,
            closed_question.multi_choice_response_count) == (1, 0, 1)
    open_question.refresh_from_db()
    assert (open_question.total_response_count, open_question.free_text_response_count,
            open_question.multi_choice_response_count) == (1, 1, 0)
    hybrid_original.refresh_from_db()
    assert (hybrid_original.total_response_count, hybrid_original.free_text_response_count,
            hybrid_original.multi_choice_response_count) == (1, 1, 1)

    # the sibling has no v1 representation: counts come from its option rows
    hybrid_sibling.refresh_from_db()
    assert (hybrid_sibling.total_response_count, hybrid_sibling.free_text_response_count,
            hybrid_sibling.multi_choice_response_count) == (1, 0, 1)

    # original options keep their v1 response counts; sibling clones stay 0
    assert closed_question.multichoiceanswer_set.get(text="Red").response_count == 1
    assert hybrid_original.multichoiceanswer_set.get(text="Maybe").response_count == 1
    assert hybrid_sibling.multichoiceanswer_set.get(text="Maybe").response_count == 0


def test_question_type_enum_value_for_demographics():
    assert Question.QuestionType.DEMOGRAPHIC.value == "demographic"


def test_fill_response_text(v1_consultation):
    _fill_response_text(v1_consultation)

    responses = list(Response.objects.filter(question__consultation=v1_consultation))
    copied = [r for r in responses if r.free_text not in (None, "")]
    untouched = [r for r in responses if r.free_text in (None, "")]
    # every content-bearing row is dual-written; empty/None rows stay untyped
    assert {r.text for r in copied} == {"Hello world", "Specify other"}
    assert all(r.text == r.free_text for r in copied)
    assert all(r.text is None for r in untouched)

    # idempotent: a second pass copies nothing new
    assert (
        Response.objects.filter(
            question__consultation=v1_consultation, text__isnull=True, free_text__isnull=False
        )
        .exclude(free_text="")
        .update(text=F("free_text"))
        == 0
    )


def _question_by_type(consultation, question_type, with_closed_link=None):
    matches = [
        q
        for q in consultation.question_set.all()
        if q.type == question_type
        and (with_closed_link is None or (q.closed_question_id is not None) == with_closed_link)
    ]
    assert len(matches) == 1
    return matches[0]


def test_backfill_question_types(v1_consultation):
    _backfill_question_types(v1_consultation)

    questions = list(v1_consultation.question_set.all())
    open_questions = [q for q in questions if q.type == Question.QuestionType.OPEN]
    closed_questions = [q for q in questions if q.type == Question.QuestionType.CLOSED]
    untyped = [q for q in questions if q.type is None]
    assert len(open_questions) == 2  # free-text-only original + hybrid original
    assert len(closed_questions) == 2  # multiple-choice-only original + hybrid sibling
    assert len(untyped) == 1  # neither-flag question stays untyped (prod audit: none exist)
    assert all(
        q.status == Question.ThemeStatus.CONFIGURED for q in open_questions + closed_questions
    )

    hybrid_original = next(q for q in open_questions if q.closed_question_id is not None)
    sibling = hybrid_original.closed_question
    assert sibling in closed_questions
    assert {answer.text for answer in sibling.multichoiceanswer_set.all()} == {"Maybe"}

    # Nothing on the original row was moved: its text and chosen option stay
    hybrid_response = Response.objects.get(question=hybrid_original, free_text="Specify other")
    assert hybrid_response.chosen_options.count() == 1


def test_convert_multiple_choice_to_responses(v1_consultation):
    _backfill_question_types(v1_consultation)
    closed_question = next(
        q
        for q in v1_consultation.question_set.all()
        if q.type == Question.QuestionType.CLOSED
        and {a.text for a in q.multichoiceanswer_set.all()} == {"Red", "Blue"}
    )
    hybrid_sibling = next(
        q
        for q in v1_consultation.question_set.all()
        if q.type == Question.QuestionType.CLOSED
        and {a.text for a in q.multichoiceanswer_set.all()} == {"Maybe"}
    )

    _convert_multiple_choice_to_responses(v1_consultation)

    # closed-only question: one row per selected option, original untouched
    option_rows = closed_question.response_set.exclude(text__isnull=True)
    assert {(row.text) for row in option_rows} == {"Red", "Blue"}
    assert option_rows.count() == 2

    # hybrid: option row lands on the closed sibling, keyed by option text
    hybrid_rows = hybrid_sibling.response_set.exclude(text__isnull=True)
    assert [row.text for row in hybrid_rows] == ["Maybe"]

    # idempotent: re-running converts nothing new
    total_rows = Response.objects.filter(question__consultation=v1_consultation).count()
    _convert_multiple_choice_to_responses(v1_consultation)
    assert Response.objects.filter(question__consultation=v1_consultation).count() == total_rows


def test_convert_skips_untyped_questions_with_options(v1_consultation):
    neither_flag_question = v1_consultation.question_set.get(
        has_free_text=False, has_multiple_choice=False
    )
    respondent = RespondentFactory(consultation=v1_consultation)
    neither_flag_response = ResponseFactory(
        question=neither_flag_question, respondent=respondent, free_text=None
    )
    neither_flag_response.chosen_options.add(
        MultiChoiceAnswerFactory(question=neither_flag_question, text="Odd")
    )

    _backfill_question_types(v1_consultation)
    _convert_multiple_choice_to_responses(v1_consultation)

    # the untyped question is left alone: still untyped, original row untouched
    untyped = v1_consultation.question_set.filter(has_free_text=False, has_multiple_choice=False)
    assert untyped.count() == 1 and untyped.get() == neither_flag_question
    neither_flag_response.refresh_from_db()
    assert neither_flag_response.text is None
    assert neither_flag_response.chosen_options.count() == 1
    assert not neither_flag_question.response_set.exclude(text__isnull=True).exists()

