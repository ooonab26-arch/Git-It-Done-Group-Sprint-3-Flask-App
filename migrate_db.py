# migrate_to_postgres.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *
from app import create_app

# Local DB
local_engine = create_engine("sqlite:///instance/events.db")
LocalSession = sessionmaker(bind=local_engine)
local_session = LocalSession()

# Cloud DB
app = create_app()
app.app_context().push()
cloud_session = db.session

# Migration helper
def migrate_table(model):
    for row in local_session.query(model).all():
        cloud_instance = model(**{c.name: getattr(row, c.name) for c in row.__table__.columns if c.name != "id"})
        cloud_session.add(cloud_instance)
    cloud_session.commit()
    print(f"Migrated {model.__tablename__}")

# Migrate in order to satisfy FK constraints
for model in [User, Advertisement, Partners, Organizer, Event_Type, Events, ProcessedFile]:
    migrate_table(model)

print("All tables migrated successfully!")
