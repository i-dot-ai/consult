import pytest


@pytest.mark.django_db
def test_nav_links(django_app):
    homepage = django_app.get("/")
    assert "Use machine learning to help you understand consultation responses" in homepage

    how_it_works_page = homepage.click("How it works", index=0)
    assert "You can see the code on" in how_it_works_page

    schema_page = how_it_works_page.click("Data schema", index=0)
    assert "JSON schemas" in schema_page

    data_sharing_page = schema_page.click("Data sharing", index=0)
    assert "data sharing agreement" in data_sharing_page

    get_involved_page = data_sharing_page.click("Get involved", index=0)
    assert "register your interest" in get_involved_page
