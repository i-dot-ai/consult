from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command

from consultations.models import Consultation, Response
from consultations.services.legacy_answers import count_unmatched_legacy_answers
from consultations.services.migrate_v1_to_v2 import migrate_consultation_to_v2
from factories import ConsultationFactory

pytestmark = pytest.mark.django_db


def _run(*args):
    output = StringIO()
    call_command("migrate_v1_consultations", *args, stdout=output)
    return output.getvalue()


def test_unmatched_count_is_every_selected_option_before_migration(legacy_consultation):
    assert count_unmatched_legacy_answers(legacy_consultation) == 3


def test_dry_run_reports_and_exits_non_zero_without_writing(legacy_consultation):
    with pytest.raises(CommandError, match="nothing was changed"):
        _run("--dry-run")

    legacy_consultation.refresh_from_db()
    assert legacy_consultation.migrated_at is None
    assert Response.objects.filter(question__consultation=legacy_consultation).count() == 2


def test_migrates_every_unmigrated_consultation(legacy_consultation):
    output = _run()

    legacy_consultation.refresh_from_db()
    assert legacy_consultation.migrated_at is not None
    assert count_unmatched_legacy_answers(legacy_consultation) == 0
    assert "1 migrated, 0 failed" in output


def test_dry_run_is_quiet_once_everything_is_migrated(legacy_consultation):
    _run()

    output = _run("--dry-run")

    assert "0 consultations unmigrated, 0 selected options unmatched" in output


def test_rerun_is_a_no_op(legacy_consultation):
    _run()
    rows_after_first_run = Response.objects.filter(
        question__consultation=legacy_consultation
    ).count()

    _run()

    assert Response.objects.filter(question__consultation=legacy_consultation).count() == (
        rows_after_first_run
    )


def test_one_failure_does_not_stop_the_rest(legacy_consultation):
    other = ConsultationFactory(is_v1=True)

    def failing_for_other(consultation):
        if consultation.id == other.id:
            raise RuntimeError("boom")
        return migrate_consultation_to_v2(consultation)

    with (
        patch(
            "consultations.management.commands.migrate_v1_consultations.migrate_consultation_to_v2",
            side_effect=failing_for_other,
        ),
        pytest.raises(CommandError, match=str(other.id)),
    ):
        _run()

    legacy_consultation.refresh_from_db()
    assert legacy_consultation.migrated_at is not None
    other.refresh_from_db()
    assert other.migrated_at is None


def test_consultation_option_limits_the_run(legacy_consultation):
    other = ConsultationFactory(is_v1=True)

    _run("--consultation", str(other.id))

    other.refresh_from_db()
    legacy_consultation.refresh_from_db()
    assert other.migrated_at is not None
    assert legacy_consultation.migrated_at is None


def test_unknown_consultation_is_an_error():
    with pytest.raises(CommandError, match="does not exist"):
        _run("--consultation", "00000000-0000-0000-0000-000000000000")
    assert not Consultation.objects.exists()
