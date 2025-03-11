import datetime

import pytest
from django.utils import timezone
from freezegun import freeze_time

from consultation_analyser import factories


@pytest.mark.django_db
def test_datetime_theme_mapping_audited():
    with freeze_time("2021-01-01 00:00:00"):
        answer = factories.FreeTextAnswerFactory()
    with freeze_time("2021-01-02 02:01:13"):
        answer.is_theme_mapping_audited = True
        answer.save()
    with freeze_time("2021-01-03 00:00:00"):
        answer.is_theme_mapping_audited = True
        answer.save()
    assert answer.datetime_theme_mapping_audited == timezone.make_aware(
        datetime.datetime(2021, 1, 2, 2, 1, 13)
    )
