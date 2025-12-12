import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from app import create_app
from models import db

@pytest.fixture
def app():
    app = create_app(testing=True)
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()

@pytest.fixture
def client(app):
    return app.test_client()