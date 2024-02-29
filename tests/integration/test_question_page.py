def test_get_question_page(client):
    response = client.get("/questions/how-should-funding-be-allocated")
    assert "How should funding be allocated?" in str(response.content)
