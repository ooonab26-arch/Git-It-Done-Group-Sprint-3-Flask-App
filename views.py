from flask_sqlalchemy import SQLAlchemy
from models import db, Events
from flask import Flask, Blueprint, render_template
from sqlalchemy import extract, func
from datetime import datetime

main_blueprint = Blueprint('homepage', __name__)

@main_blueprint.route('/')
def dashboard():
    results = (db.session.query(
        extract('month', Events.date).label('month'),
        func.sum(Events.attendance).label('total_attendance')
    ).group_by('month').order_by('month').all()
    )

    months = [datetime(1900,r.month,1).strftime('%B') for r in results]
    attendance = [r.total_attendance or 0 for r in results]

    return render_template('dashboard.html', months=months, attendance=attendance)
