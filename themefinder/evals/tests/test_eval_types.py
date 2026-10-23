"""Tests for the keys the domain types derive for naming results."""

from eval_types import Case, CaseOutcome, RunReport


def _case(case_id: str = "item-123", question_part: str | None = None) -> Case:
    metadata = {"question_part": question_part} if question_part else {}
    return Case(id=case_id, inputs={}, expected_output=None, metadata=metadata)


def _outcome(case: Case, run_index: int = 0) -> CaseOutcome:
    return CaseOutcome(case=case, output=None, scores=[], run_index=run_index)


class TestCaseKey:
    def test_prefers_question_part(self):
        assert _case(question_part="question_part_2").key == "question_part_2"

    def test_falls_back_to_id(self):
        assert _case().key == "item-123"


class TestRunReportOutcomeKey:
    def test_single_run_uses_the_plain_case_key(self):
        outcome = _outcome(_case(question_part="question_part_1"))
        report = RunReport(outcomes=[outcome])

        assert not report.repeated
        assert report.outcome_key(outcome) == "question_part_1"

    def test_repeated_run_suffixes_every_repeat_including_the_first(self):
        case = _case(question_part="question_part_1")
        first, second = _outcome(case, 0), _outcome(case, 1)
        report = RunReport(outcomes=[first, second])

        assert report.repeated
        assert report.outcome_key(first) == "question_part_1_r0"
        assert report.outcome_key(second) == "question_part_1_r1"
