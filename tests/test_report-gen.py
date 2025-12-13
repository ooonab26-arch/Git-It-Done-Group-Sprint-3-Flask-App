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

def test_get_years_returns_list(client):
    response = client.get("/api/reports/years")
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_generate_report_api(client):
    response = client.post(
        "/api/reports/generate",
        json={"year": 2024},
    )
    assert response.status_code == 200
    assert "url" in response.json

def test_generate_report_fallback(client):
    response = client.post(
        "/api/reports/generate",
        json={"year": 1900},
    )
    assert response.status_code == 200

def test_generate_report_no_year(client):
    response = client.post("/api/reports/generate", json={})
    assert response.status_code == 200
