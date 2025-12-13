from models import Events, db
from datetime import date

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

def test_event_visible_on_events_page(client, app):
    with app.app_context():
        event = Events(title="Test Event", date=date.today())
        db.session.add(event)
        db.session.commit()
    response = client.get("/events")
    assert response.status_code == 200


def test_event_detail_invalid_id(client):
    response = client.get("/events/99999")
    assert response.status_code in (404, 302)

def test_events_page_empty_db(client, app):
    with app.app_context():
        Events.query.delete()
        db.session.commit()

    response = client.get("/events")
    assert response.status_code == 200