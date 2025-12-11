from models import ProcessedFile, db, Events, Event_Type, Organizer
from flask import Blueprint, render_template
from flask_login import login_required
from flask_login import current_user
from sqlalchemy import extract, func
from datetime import datetime
import cloudinary.uploader
from calendar import month_name
from flask import request, redirect, url_for, current_app, render_template, jsonify, send_from_directory
from report_gen import read_events, summarize
import os

main_blueprint = Blueprint('homepage', __name__)
    
@main_blueprint.route('/')
def home():     
    if current_user.is_authenticated:
        return redirect(url_for('homepage.dashboard'))
    return redirect(url_for('auth.signIn'))

@main_blueprint.route('/api/v1/dashboard')
@login_required
def dashboard():
    results = (db.session.query(
        extract('month', Events.date).label('month'),
        func.count(Events.id).label('event_count'),
        func.sum(Events.attendance).label('total_attendance')
    ).group_by('month').order_by('month').all()
    )

    attendance_total = db.session.query(
        func.sum(Events.attendance)
    ).scalar()

    event_total = db.session.query(
        func.count(Events.id)
    ).scalar()

    months = [datetime(1900,int(r.month),1).strftime('%B') for r in results]
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

# ---- Event category percentage breakdown ----
    category_results = (
        db.session.query(
            Event_Type.name.label("category"),
            func.count(Events.id).label("count")
        )
        .join(Events, Events.type_id == Event_Type.id)
        .group_by(Event_Type.name)
        .all()
    )

    total_event_count = sum(r.count for r in category_results)

    category_percentages = [
        {
            "category": r.category,
            "count": r.count,
            "percentage": round((r.count / total_event_count) * 100, 2) if total_event_count else 0
        }
        for r in category_results
    ]

  # --- Suggest top 4 upcoming events ---
    popular_month = (
        db.session.query(
            extract('month', Events.date).label('month'),
            func.sum(Events.attendance).label('total_attendance')
        )
        .group_by('month')
        .order_by(func.sum(Events.attendance).desc())
        .first()
    )

    suggested_month = popular_month.month if popular_month else datetime.now().month

    top_events = (
        db.session.query(
            Events.id,
            Events.date,
            Event_Type.name.label('category'),
            Events.attendance
        )
        .join(Event_Type, Events.type_id == Event_Type.id)
        .order_by(Events.attendance.desc())
        .limit(4)
        .all()
    )

    suggestions = [
        {
            "event_type": e.category,
            "day": e.date.day,
            "month": month_name[e.date.month]
        }
        for e in top_events
    ]

    # print(suggestions)

    return render_template('dashboard.html', months=all_months, attendance=attendance_twelve_months, growth=growth_twelve_months, category_percentages=category_percentages, suggestions=suggestions, attendance_total = attendance_total, event_total = event_total)

def getEventsList():
    events = (
        db.session.query(Events, Organizer)
        .outerjoin(Organizer, Organizer.id == Events.lead_organizer)
        .join(Event_Type, Events.type_id == Event_Type.id)
        .order_by(Events.date.desc())
        .all()
    )

    event_list = []
    for e, organizer in events:
        partner_names = [p.name for p in e.partners] if e.partners else []

        event_list.append({
            "id": e.id,
            "title": e.title,
            "date": e.date,
            "type_name": e.event_type.name,
            "location": e.location,
            "attendance": e.attendance,
            "description": e.description,
            "lead_organizer": organizer.name if organizer else "N/A",
            "partners": ", ".join(partner_names),
            "poster_url": e.poster_url
        })
    
    return event_list


@main_blueprint.route('/api/v1/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = Events.query.get(event_id)
    
    if not event:
        return jsonify({"error": "event not found"}) ,404
    
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({"message": "success, deleted"}), 200

@main_blueprint.route('/api/v1/events')
def events_page():
    curEventList = getEventsList()
    years = sorted({ event["date"].year for event in curEventList if event.get("date") is not None })
    specific_year = request.args.get("year", type=int)

    organizers = Organizer.query.all()
    event_types = Event_Type.query.all()
    
    if specific_year:
        curEventList = [event for event in curEventList if event.get("date") is not None and event["date"].year == specific_year]
    
    # Get event category counts
    category_results = (
        db.session.query(
            Event_Type.name.label("category"),
            func.count(Events.id).label("count")
        )
        .join(Events, Events.type_id == Event_Type.id)
        .group_by(Event_Type.name)
        .all()
    )

    categories = [{"name": r.category, "count": r.count} for r in category_results]
        
    return render_template('event.html', events=curEventList,years=years,categories=categories,specific_year=specific_year, organizers=organizers, event_types=event_types)


@main_blueprint.route('/api/v1/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Events.query.get(event_id)
    
    if not event:
        return jsonify({"error": "event not found"}) ,404
    
    return jsonify({
        "id": event.id,
        "title": event.title,
        "date": event.date.strftime("%Y-%m-%d"),
        "type_id": event.type_id,
        "location": event.location,
        "attendance": event.attendance,
        "description" : event.description,
        "lead_organizer" : event.lead_organizer    
    })
  
@main_blueprint.route('/profile')
def profile():
    return render_template('profile.html')

@main_blueprint.route('/report')
def report_page():
    # Get all events
    curEventList = getEventsList()

    # ---- Aggregate attendance by month ----
    results = (
        db.session.query(
            extract('month', Events.date).label('month'),
            func.count(Events.id).label('event_count'),
            func.sum(Events.attendance).label('total_attendance')
        )
        .group_by('month')
        .order_by('month')
        .all()
    )

    months = [datetime(1900, int(r.month), 1).strftime('%B') for r in results]
    attendance = [r.total_attendance or 0 for r in results]
    total_events = [r.event_count for r in results]

    # Compute percent growth in events month-to-month
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
                percent_growth.append(round((curr - prev)/prev * 100, 2))

    # Ensure all 12 months are included
    all_months = list(month_name)[1:]
    month_to_attendance = dict(zip(months, attendance))
    month_to_growth = dict(zip(months, percent_growth))

    attendance_twelve_months = [month_to_attendance.get(m, 0) for m in all_months]
    growth_twelve_months = [month_to_growth.get(m, 0) for m in all_months]

    # ---- Event category percentage breakdown ----
    category_results = (
        db.session.query(
            Event_Type.name.label("category"),
            func.count(Events.id).label("count")
        )
        .join(Events, Events.type_id == Event_Type.id)
        .group_by(Event_Type.name)
        .all()
    )

    total_event_count = sum(r.count for r in category_results)
    category_percentages = [
        {
            "category": r.category,
            "count": r.count,
            "percentage": round((r.count / total_event_count) * 100, 2) if total_event_count else 0
        }
        for r in category_results
    ]

    # Render the report page
    return render_template(
        'report.html',
        events=curEventList,
        months=all_months,
        attendance=attendance_twelve_months,
        growth=growth_twelve_months,
        category_percentages=category_percentages
    )

    
@main_blueprint.route('/api/v1/add_event', methods=['POST'])
def add_event():
    # --- Extract form data ---
    title = request.form.get('title')
    date_obj = datetime.strptime(request.form.get('date'), "%Y-%m-%d")
    location = request.form.get('location')
    attendance = int(request.form.get('attendance'))
    description = request.form.get('description')
    lead_organizer = int(request.form.get('lead_organizer'))
    type_id = int(request.form.get('type_id'))

    # --- Create new event ---
    new_event = Events(
        title=title,
        date=date_obj,
        location=location,
        attendance=attendance,
        description=description,
        lead_organizer=lead_organizer,
        type_id=type_id
    )
    db.session.add(new_event)
    db.session.commit()  # Commit first so event has an ID

    # --- Handle poster upload ---
    poster_file = request.files.get('file_upload')
    if poster_file and poster_file.filename != "":
        upload_result = cloudinary.uploader.upload(poster_file)
        new_event.poster_url = upload_result["secure_url"]

        processed_file = ProcessedFile(
            filename=poster_file.filename,
            event=new_event
        )
        db.session.add(processed_file)
        db.session.commit()

    return redirect(url_for('homepage.events_page'))


@main_blueprint.route('/api/v1/events/<int:event_id>', methods=['POST'])
def update_event(event_id):
    event = Events.query.get(event_id)
    if not event:
        return jsonify({"error": "event not found"}), 404

    # --- Update event fields ---
    event.title = request.form.get('title')
    event.date = datetime.strptime(request.form.get('date'), "%Y-%m-%d")
    event.location = request.form.get('location')
    event.attendance = int(request.form.get('attendance'))
    event.description = request.form.get('description')
    event.lead_organizer = int(request.form.get('lead_organizer'))
    event.type_id = int(request.form.get('type_id'))

    # --- Handle poster upload ---
    poster_file = request.files.get('file_upload')
    if poster_file and poster_file.filename != "":
        upload_result = cloudinary.uploader.upload(poster_file)
        event.poster_url = upload_result["secure_url"]

        # Check if a ProcessedFile already exists for this event
        processed_file = ProcessedFile.query.filter_by(event_id=event.id).first()
        if processed_file:
            processed_file.filename = poster_file.filename
        else:
            new_file = ProcessedFile(
                filename=poster_file.filename,
                event=event
            )
            db.session.add(new_file)


    db.session.commit()
    return redirect(url_for('homepage.events_page'))



@main_blueprint.post('/api/v1/reports/generate')
def generate_report():
    payload = request.get_json(silent=True) or {}
    y = payload.get("year")

    year = int(y) if isinstance(y, (int, str)) and str(y).isdigit() else None

    rows = read_events(year)
    fallback_used = False

    if year and not rows:
        rows = read_events(None)
        fallback_used = True

    summary = summarize(rows)

    title = f"Events Report {year}" if year and not fallback_used else "Events Report (All Years)"
    note = "" if (year and not fallback_used) else (
        f"<p style='color:#6b7280'>No rows found for {year}. Showing all years.</p>" if year else ""
    )

    # Chart prep
    by_month = summary["by_month"]
    months = list(by_month.keys())
    attendance = [by_month[m]["events"] for m in months]

    type_counts = {}
    for r in rows:
        t = r["type"] or "Unknown"
        type_counts[t] = type_counts.get(t, 0) + 1

    js_pie_labels = list(type_counts.keys())
    js_pie_values = list(type_counts.values())


    html = render_template(
        "standalone_report.html",   
        title=title,
        note=note,
        summary=summary,
        rows=rows,
        months=months,
        attendance=attendance,   
        js_pie_labels=js_pie_labels,
        js_pie_values=js_pie_values,
    )

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"report_{year if year else 'all'}_{ts}.html"

    out_dir = os.path.join(current_app.instance_path, "reports")
    os.makedirs(out_dir, exist_ok=True)

    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(html)

    return jsonify({
        "report_id": fname,
        "url": f"/reports/files/{fname}",
        "format": "html"
    })

@main_blueprint.route('/api/v1/reports/files/<filename>')
def serve_report(filename):
    out_dir = os.path.join(current_app.instance_path, "reports")
    return send_from_directory(out_dir, filename)

@main_blueprint.get('/api/events/years')
def api_get_years():
    """
    Return a JSON list of distinct years that have events in the DB,
    e.g. [2023, 2024, 2025].
    """
    years = (
        db.session.query(extract('year', Events.date).label('year'))
        .group_by('year')
        .order_by('year')
        .all()
    )
    year_list = [int(row.year) for row in years]
    return jsonify(year_list)

@main_blueprint.get('/api/v1/attendance')
def api_attendance_by_year():
    # Optional year filter
    year = request.args.get("year", type=int)

    query = db.session.query(
        extract('month', Events.date).label('month'),
        func.sum(Events.attendance).label('total_attendance'),
        func.count(Events.id).label('event_count')
    )

    if year:
        query = query.filter(extract('year', Events.date) == year)

    results = query.group_by('month').order_by('month').all()

    # Ensure all 12 months are present
    all_months = list(month_name)[1:]
    month_to_attendance = {datetime(1900,int(r.month),1).strftime('%B'): r.total_attendance or 0 for r in results}
    month_to_count = {datetime(1900,int(r.month),1).strftime('%B'): r.event_count or 0 for r in results}

    attendance_twelve_months = [month_to_attendance.get(m, 0) for m in all_months]
    count_twelve_months = [month_to_count.get(m, 0) for m in all_months]

    return jsonify({
        "months": all_months,
        "attendance": attendance_twelve_months,
        "events": count_twelve_months
    })

@main_blueprint.get('/api/v1/upload_poster/<int:event_id>')
def upload_poster(event_id):
    file = request.files['poster']
    upload_result = cloudinary.uploader.upload(file)
    event = Events.query.get(event_id)

    poster_url = upload_result["secure_url"]
    event = Events.query.get(event_id)
    event.poster_url = poster_url
    db.session.commit()

    return redirect(url_for('event_detail', event_id=event_id))
