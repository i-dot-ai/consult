import pytest


from tests.factories import ConsultationFactory


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    ConsultationFactory(with_question=True)
    resp = django_app.get("/")
    assert resp.status_code == 200
