from flask_sqlalchemy import SQLAlchemy
from models import db, Events
from flask import Flask, Blueprint, render_template
from sqlalchemy import extract, func
from datetime import datetime
from calendar import month_name

main_blueprint = Blueprint('homepage', __name__)

@main_blueprint.route('/')
def dashboard():
    results = (db.session.query(
        extract('month', Events.date).label('month'),
        func.count(Events.id).label('event_count'),
        func.sum(Events.attendance).label('total_attendance')
    ).group_by('month').order_by('month').all()
    )

    months = [datetime(1900,r.month,1).strftime('%B') for r in results]
    attendance = [r.total_attendance or 0 for r in results]
    total_events = [r.event_count for r in results]
   
    percent_growth = []
    for i in range(len(total_events)):
        if i == 0:
            percent_growth.append(0)
        else:
            prev = total_events[i-1]
            curr = total_events[i]
            if prev == 0:
                percent_growth.append(0)
            else:
                percent_growth.append(round((curr-prev)/prev * 100, 2))

    # Ensure all 12 months are shown in the dashboard even if no data is present
    all_months = list(month_name)[1:] 
    month_to_attendance = dict(zip(months, attendance))
    month_to_growth = dict(zip(months, percent_growth))

    attendance_twelve_months = [month_to_attendance.get(m, 0) for m in all_months]
    growth_twelve_months = [month_to_growth.get(m, 0) for m in all_months]

    return render_template('dashboard.html', months=all_months, attendance=attendance_twelve_months, growth=growth_twelve_months)
