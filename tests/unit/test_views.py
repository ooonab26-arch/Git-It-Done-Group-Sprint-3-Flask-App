def test_dashboard_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_events_page(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert b"Events" in response.data