def test_download_valid_schema(client):
    valid_schemas = ["consultation", "consultation_response", "consultation_with_responses"]
    for schema in valid_schemas:
        resp = client.get(f"/schema/{schema}_schema.json")
        assert b"$defs" in resp.content


def test_download_invalid_schema(client):
    resp = client.get("/schema/totally_made_up_schema.json")
    assert resp.status_code == 404


def test_download_malicious_schema(client):
    resp = client.get("/schema/../public_schema.py.json")
    assert resp.status_code == 404
