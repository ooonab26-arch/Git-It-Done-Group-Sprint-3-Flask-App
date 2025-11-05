from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    position = db.Column(db.String(200), nullable=False)
    # events = db.relationship('Events', backref='user', lazy=True)

class Events(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    date = db.Column(db.Date, nullable=False)
    attendance = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(80), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Foreign Keys (table names now match __tablename__ below)
    advert_id = db.Column(db.Integer, db.ForeignKey('advertisement.id'), nullable=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id'), nullable=True)
    lead_organizer = db.Column(db.Integer, db.ForeignKey('organizers.id'), nullable=True)
    type_id = db.Column(db.Integer, db.ForeignKey('event_type.id'), nullable=True)

class Advertisement(db.Model):
    __tablename__ = "advertisement"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    events = db.relationship('Events', backref='advertisement', lazy=True)

class Partners(db.Model):
    __tablename__ = "partners"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

class Organizer(db.Model):
    __tablename__ = "organizers"  # plural to match FK 'organizers.id'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

class Event_Type(db.Model):
    __tablename__ = "event_type"  # avoids 'event__type' auto-name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    events = db.relationship('Events', backref='event_type', lazy=True)

# Association tables (FKs now match table names above)
event_organizers = db.Table(
    'event_organizers',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('organizer_id', db.Integer, db.ForeignKey('organizers.id'), primary_key=True),
)

event_partners = db.Table(
    'event_partners',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('partner_id', db.Integer, db.ForeignKey('partners.id'), primary_key=True),
)
