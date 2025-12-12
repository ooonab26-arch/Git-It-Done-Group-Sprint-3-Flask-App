def test_dashboard_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_events_page(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert b"Events" in response.data

def test_dashboard_redirects_when_logged_out(client):
    response = client.get("/")
    assert response.status_code == 200

def test_profile_page(client):
    client.post(
        "/auth/api/v1/auth/signup",
        data={"name": "P", "email": "p@p.com", "password": "pass"},
    )
    response = client.get("/profile")
    assert response.status_code == 200
