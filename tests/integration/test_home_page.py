import pytest

from consultation_analyser.factories import ConsultationFactory


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    consultation = ConsultationFactory(with_question=True)
    question = consultation.section_set.first().question_set.first()
    homepage = django_app.get("/")
    question_page = homepage.click(f"{question.text}")

    assert "Question summary" in question_page
    assert f"{question.text}" in question_page


@pytest.mark.django_db
def test_nav_links(django_app):
    homepage = django_app.get("/")
    assert len(homepage.html.select(".govuk-header__navigation-item--active")) == 0

    schema_page = homepage.click("Data schema")

    assert len(schema_page.html.select(".govuk-header__navigation-item--active")) == 1
    assert "data schema" in schema_page
