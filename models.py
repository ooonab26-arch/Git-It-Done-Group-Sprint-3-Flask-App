from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique = True, nullable=False)
    position = db.Column(db.String(200), nullable=False)
    # events = db.relationship('Events', backref='user', lazy=True) Consider adding this in if I want to track which user (collyn or SW) edited an event

class Events(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    date = db.Column(db.Date, nullable=False)
    attendance = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Foreign Keys
    advert_id = db.Column(db.Integer, db.ForeignKey('advertisement.id'), nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id'))
    lead_organizer = db.Column(db.Integer, db.ForeignKey('organizers.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('event_type.id'), nullable=False)

class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(200), nullable=False)
    events = db.relationship('Events', backref='event_type', lazy=True)

class Partners(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

class Organizer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

class Event_Type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    events = db.relationship('Events', backref='event_type', lazy=True)

# Association tables for 'many to many' relationships in DB
event_organizers = db.Table('event_organizers',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('organizer_id', db.Integer, db.ForeignKey('organizers.id'), primary_key=True)
)

event_partners = db.Table('event_partners', 
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('partner_id', db.Integer, db.ForeignKey('partners.id'), primary_key=True))