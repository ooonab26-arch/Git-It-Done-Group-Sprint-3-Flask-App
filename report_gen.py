from datetime import datetime
from models import db, Events, Event_Type
from sqlalchemy import extract


def read_events(year: int | None = None):
    """
    Query the Events table and return rows in the old CSV-like dict format.
    Supports year filtering.
    """
    query = db.session.query(Events).join(Event_Type, isouter=True)

    if year:
        query = query.filter(extract('year', Events.date) == year)

    events = query.order_by(Events.date.asc()).all()

    rows = []
    for e in events:
        rows.append({
            "title": e.title,
            "date": e.date,
            "start_time": e.start_time.strftime("%I:%M %p") if e.start_time else "",
            "end_time": e.end_time.strftime("%I:%M %p") if e.end_time else "",
            "attendance": e.attendance or 0,
            "location": e.location or "",
            "type": e.event_type.name if e.event_type else "Unknown",
        })

    return rows


def summarize(rows):
    total_events = len(rows)
    total_attendees = sum(r["attendance"] for r in rows)

    by_month = {}
    for r in rows:
        if not r["date"]:
            continue

        m = r["date"].strftime("%b")
        if m not in by_month:
            by_month[m] = {"events": 0, "attendance": 0}

        by_month[m]["events"] += 1
        by_month[m]["attendance"] += r["attendance"]

    return {
        "total_events": total_events,
        "total_attendees": total_attendees,
        "by_month": by_month
    }
