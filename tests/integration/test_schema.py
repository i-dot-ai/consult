import json


def test_get_public_schema_page(django_app):
    # Given I am viewing the /schema page
    schema_page = django_app.get("/schema/")

    # When I look for information about the schema
    # Then I should see the headings
    assert "Consultation data schema" in schema_page

    # And I should see the entity documentation
    assert "Consultation is the top-level object describing a consultation" in schema_page

    # And I should see the JSON schema and examples
    upload_schema = schema_page.html.select("div[data-qa='consultation-with-responses-schema'] > pre > code")[
        0
    ].get_text()
    assert "$defs" in upload_schema

    # representative because there are answers
    upload_example = schema_page.html.select("div[data-qa='consultation-with-responses-example'] > pre > code")[
        0
    ].get_text()

    parsed_example = json.loads(upload_example)
    assert parsed_example["consultation"]
    assert parsed_example["consultation_responses"]

    assert "questions" in upload_example
    assert "answers" in upload_example
