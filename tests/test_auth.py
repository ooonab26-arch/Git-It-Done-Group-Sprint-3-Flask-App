def test_signup_page_loads(client):
    response = client.get("/auth/api/v1/auth/signup")
    assert response.status_code == 200
    assert b"Sign" in response.data


def test_user_signup(client, app):
    response = client.post(
        "/auth/api/v1/auth/signup",
        data={
            "name": "Tester",
            "email": "tester@example.com",
            "password": "pass123",
            "position": "Staff"
        },
        follow_redirects=True
    )
    assert response.status_code == 200


def test_signin_invalid_credentials(client):
    response = client.post(
        "/auth/api/v1/auth/signin",
        data={"email": "nope@example.com", "password": "wrong"},
        follow_redirects=True,
    )
    assert b"Invalid email" in response.data

def test_logout_requires_login(client):
    response = client.get("/auth/api/v1/auth/logout")
    assert response.status_code == 302

def test_logout_logged_in(client):
    client.post(
        "/auth/api/v1/auth/signup",
        data={"name": "A", "email": "a@a.com", "password": "pass"},
    )

    response = client.get("/auth/api/v1/auth/logout", follow_redirects=True)
    assert b"Sign in" in response.data

def test_google_login_redirect(client):
    response = client.get("/auth/google/login")
    assert response.status_code == 302
    assert "accounts.google.com" in response.location


def test_signup_duplicate_user(client):
    client.post(
        "/auth/api/v1/auth/signup",
        data={"name": "Dup", "email": "dup@test.com", "password": "123"},
        follow_redirects=True,
    )

    response = client.post(
        "/auth/api/v1/auth/signup",
        data={"name": "Dup", "email": "dup@test.com", "password": "123"},
        follow_redirects=True,
    )

    assert b"already exists" in response.data.lower()


def test_google_callback_without_token(client, monkeypatch):
    from auth import oauth
    monkeypatch.setattr(oauth.google, "authorize_access_token", lambda: {})
    monkeypatch.setattr(oauth.google, "parse_id_token", lambda token: None)
    response = client.get("/auth/google/callback", follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign In" in response.data or b"Login" in response.data
