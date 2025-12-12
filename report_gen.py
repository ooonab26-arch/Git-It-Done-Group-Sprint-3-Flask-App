from flask import Blueprint, request, jsonify, render_template, current_app, send_from_directory
from models import db, Events, Event_Type
from sqlalchemy import extract
from datetime import datetime
from collections import Counter
import os

reports_bp = Blueprint("reports", __name__)

# -------------------------
# Return available years
# -------------------------
@reports_bp.get("/events/years")
def api_get_years():
    years = (
        db.session.query(extract("year", Events.date).label("year"))
        .group_by("year")
        .order_by("year")
        .all()
    )
    year_list = [int(y.year) for y in years]
    return jsonify(year_list)

# Alias so tests expecting /api/reports/years still work
@reports_bp.get("/years")
def api_get_years_plain():
    return api_get_years()

# -------------------------
# Read events by year
# -------------------------
def read_events(year=None):
    q = db.session.query(Events, Event_Type.name.label("type")) \
        .join(Event_Type, Events.type_id == Event_Type.id, isouter=True)

    if year:
        q = q.filter(extract("year", Events.date) == year)

    rows = []
    for e, type_name in q.all():
        rows.append({
            "title": e.title,
            "date": e.date,
            "start": e.start_time,
            "end": e.end_time,
            "attendance": e.attendance,
            "location": e.location,
            "type": type_name or "Unknown"
        })
    return rows

# -------------------------
# Summaries for charts
# -------------------------
def summarize(rows):
    by_month = {m: {"events": 0, "attendance": 0} for m in range(1, 13)}

    for r in rows:
        m = r["date"].month
        by_month[m]["events"] += 1
        by_month[m]["attendance"] += (r["attendance"] or 0)

    return {
        "total_events": sum(v["events"] for v in by_month.values()),
        "total_attendees": sum(v["attendance"] for v in by_month.values()),
        "by_month": by_month
    }

# -------------------------
# Generate report
# -------------------------
@reports_bp.route("/generate", methods=["GET", "POST"])
def api_generate_report():
    data = (
        request.get_json(silent=True)
        if request.method == "POST"
        else request.args
    )
    year = data.get("year")
    year = int(year) if year and str(year).isdigit() else None

    rows = read_events(year)
    fallback = False

    if year and not rows:
        fallback = True
        rows = read_events(None)

    summary = summarize(rows)
    
    months = [summary['by_month'][m]['events'] for m in range(1, 13)]
    attendance = [summary['by_month'][m]['attendance'] for m in range(1, 13)]

    type_counter = Counter(r["type"] for r in rows)
    js_pie_labels = list(type_counter.keys())
    js_pie_values = list(type_counter.values())

    html = render_template(
        "standalone_report.html",
        title=f"Events Report {year}" if year and not fallback else "Events Report (All Years)",
        summary=summary,
        rows=rows,
        year=year,
        months=months,
        attendance=attendance,
        js_pie_labels=js_pie_labels,
        js_pie_values=js_pie_values,
    )

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"report_{year if year else 'all'}_{ts}.html"

    out_dir = os.path.join(current_app.instance_path, "reports")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as fp:
        fp.write(html)

    return jsonify({
        "url": f"/api/reports/files/{fname}",
        "report_id": fname
    })

# -------------------------
# Serve saved report files
# -------------------------
@reports_bp.route("/files/<filename>")
def serve_report(filename):
    out_dir = os.path.join(current_app.instance_path, "reports")
    return send_from_directory(out_dir, filename)