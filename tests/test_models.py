from models import User

def test_user_creation(app):
    u = User(name="Test User", email="test@example.com", position="Staff")
    assert u.name == "Test User"
    assert u.email == "test@example.com"
    assert u.position == "Staff"


def test_password_hashing(app):
    u = User(name="Test", email="test2@example.com", position="Staff")
    u.set_password("password123")
    assert u.check_password("password123")
    assert not u.check_password("wrongpassword")