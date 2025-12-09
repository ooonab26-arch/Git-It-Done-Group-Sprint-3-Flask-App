from app import create_app
from models import db, Events

app = create_app()

with app.app_context():
    # db.create_all()
    print(Events.query.count())
