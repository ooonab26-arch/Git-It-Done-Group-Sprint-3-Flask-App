def test_get_years_empty(client):
    response = client.get("/api/reports/years")
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_generate_report_standalone(client):
    response = client.get("/api/reports/generate?year=2024")
    assert response.status_code == 200
    data = response.get_json()
    assert "url" in data
    assert "report_id" in data