import datetime

import pytest
from freezegun import freeze_time

from consultation_analyser import factories


@pytest.mark.django_db
def test_get_datetime_audited():
    with freeze_time("2021-01-01 00:00:00"):
        answer = factories.FreeTextAnswerFactory()
    with freeze_time("2021-01-02 02:01:13"):
        answer.is_theme_mapping_audited = True
        answer.save()
    with freeze_time("2021-01-03 00:00:00"):
        answer.is_theme_mapping_audited = False
        answer.save()
    assert answer.get_datetime_audited() == datetime.datetime(2021, 1, 3, 2, 1, 13)
