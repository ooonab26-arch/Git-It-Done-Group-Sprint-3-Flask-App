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