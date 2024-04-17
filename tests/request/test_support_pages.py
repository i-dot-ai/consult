import pytest


@pytest.mark.django_db
def test_no_login_ml_pipeline_page_support(client):
    assert client.get("/support/ml-pipeline-test/").status_code == 302
