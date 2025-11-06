from flask import jsonify, request
from models import db, Events
from flask import Flask, jsonify, request, send_file, send_from_directory, render_template, current_app
from flask_sqlalchemy import SQLAlchemy
from load_data import load_events
from views import main_blueprint
import os
import io
import csv
from datetime import datetime

CSV_PATH = os.environ.get("EVENTS_CSV", os.path.join(
    os.path.dirname(__file__), "SW_Events.csv"))


def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()

        if Events.query.count() == 0:
            print("No data found in database - begin loading csv data")
            load_events()
        else:
            print("Data already loaded - skipping csv import")

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, "reports"), exist_ok=True)

    # --- helpers ---
    def read_csv(year: int | None = None):
        rows = []
        path = os.environ.get("EVENTS_CSV", os.path.join(
            os.path.dirname(__file__), "SW_Events.csv"))
        if not os.path.exists(path):
            return rows
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                raw_date = (r.get("Date") or r.get("date") or "").strip()
                dt = None
                if raw_date:
                    try:
                        if "-" in raw_date and len(raw_date.split("-")[-1]) == 2:
                            dt = datetime.strptime(raw_date, "%d-%b-%y").date()
                        else:
                            dt = datetime.fromisoformat(raw_date).date()
                    except Exception:
                        dt = None

                def intval(x):
                    try:
                        # handle "", " ", "1,200"
                        return int(str(x).replace(",", "").strip())
                    except Exception:
                        return 0

                title = (
                    r.get("Name of Event/Activity")
                    or r.get("Event Title")
                    or r.get("Title")
                    or r.get("title")
                    or ""
                )

                if year and (not dt or dt.year != year):
                    continue

                rows.append({
                    "title": title,
                    "date": dt,
                    "start_time": (r.get("Start Time") or r.get("start_time") or "").strip(),
                    "end_time": (r.get("End Time") or r.get("end_time") or "").strip(),
                    "attendance": intval(r.get("Attendance") or r.get("attendance") or 0),
                    "location": r.get("Location") or r.get("location") or "",
                    "type": r.get("Type") or r.get("Event Type") or r.get("type") or "",
                })
        return rows

    def summarize(rows):
        total_events = len(rows)
        total_attendees = sum(r['attendance'] for r in rows)
        by_month = {}
        for r in rows:
            if not r['date']:
                continue
            m = r['date'].strftime('%b')
            if m not in by_month:
                by_month[m] = {'events': 0, 'attendance': 0}
            by_month[m]['events'] += 1
            by_month[m]['attendance'] += r['attendance']
        return {'total_events': total_events, 'total_attendees': total_attendees, 'by_month': by_month}

    # ------- report & export endpoints -------
    @app.get('/api/reports/export.csv')
    def export_csv():
        year = request.args.get('year', type=int)
        rows = read_csv(year)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['title', 'date', 'start_time', 'end_time',
                   'attendance', 'location', 'type'])
        for r in rows:
            d = r['date'].isoformat() if r['date'] else ''
            w.writerow([r['title'], d, r['start_time'], r['end_time'],
                       r['attendance'], r['location'], r['type']])
        mem = io.BytesIO(buf.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(mem, as_attachment=True,
                         download_name=f"events_{year if year else 'all'}.csv",
                         mimetype='text/csv')

    @app.post('/api/reports/generate')
    def generate_report():
        if request.method == 'GET':
            year = request.args.get('year', type=int)
        else:
            payload = request.get_json(silent=True) or {}
            y = payload.get('year')
            year = int(y) if isinstance(
                y, (int, str)) and str(y).isdigit() else None

        rows = read_csv(year)
        fallback_used = False
        if year and not rows:
            # No rows for the requested year -> fall back to "all"
            rows = read_csv(year=None)
            fallback_used = True

        summary = summarize(rows)

        # build HTML
        title = f"Events Report {year}" if year and not fallback_used else "Events Report (All Years)"
        note = "" if (year and not fallback_used) else (
            f"<p style='color:#6b7280'>No rows found for {year}. Showing all years.</p>" if year else ""
        )

        html = [
            "<!doctype html><meta charset='utf-8'><title>Events Report</title>",
            "<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:24px}"
            ".card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:12px 0}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #e5e7eb;padding:8px;text-align:left}th{background:#f8fafc}"
            "h1{margin:0 0 16px}</style>",
            f"<h1>{title}</h1>",
            note,
            f"<div class='card'><b>Total Events:</b> {summary['total_events']}<br><b>Total Attendees:</b> {summary['total_attendees']}</div>",
            "<div class='card'><h3>By Month</h3><table><thead><tr><th>Month</th><th>Events</th><th>Attendance</th></tr></thead><tbody>"
        ]
        months = sorted(summary['by_month'].keys(),
                        key=lambda m: datetime.strptime(m, '%b').month)
        for m in months:
            html.append(
                f"<tr><td>{m}</td><td>{summary['by_month'][m]['events']}</td><td>{summary['by_month'][m]['attendance']}</td></tr>")
        html.append("</tbody></table></div>")
        html.append("<div class='card'><h3>Events</h3><table><thead><tr><th>Title</th><th>Date</th><th>Start</th><th>End</th><th>Attendance</th><th>Location</th><th>Type</th></tr></thead><tbody>")
        for r in rows[:100]:
            d = r['date'].isoformat() if r['date'] else ''
            html.append(
                f"<tr><td>{r['title']}</td><td>{d}</td><td>{r['start_time']}</td><td>{r['end_time']}</td><td>{r['attendance']}</td><td>{r['location']}</td><td>{r['type']}</td></tr>")
        html.append("</tbody></table></div>")
        html = ''.join(html)

        # save under instance/reports and return a public URL
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        fname = f"report_{year if year else 'all'}_{ts}.html"
        out_dir = os.path.join(app.instance_path, "reports")
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as fp:
            fp.write(html)
        return jsonify({"report_id": fname, "url": f"/reports/files/{fname}", "format": "html"})

    @app.get("/api/events/years")
    def events_years():
        """Return sorted list of years present in the CSV."""
        years = set()
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, newline="", encoding="utf-8") as f:
                rdr = csv.DictReader(f)
                for r in rdr:
                    d = (r.get("Date") or r.get("date") or "").strip()
                    if not d:
                        continue
                    y = None
                    try:
                        # supports 12-Jan-25
                        if "-" in d and len(d.split("-")[-1]) == 2:
                            y = datetime.strptime(d, "%d-%b-%y").year
                        else:
                            y = datetime.fromisoformat(d).year
                    except Exception:
                        pass
                    if y:
                        years.add(y)
        return jsonify(sorted(years))

    @app.get("/api/reports/download")
    def download_report():
        """
        Generate the same HTML report as /api/reports/generate and return it as a download.
        Usage: /api/reports/download?year=2024    (omit year for 'All years')
        """
        # --- reuse your generator logic ---
        try:
            y = request.args.get("year", type=int)
        except Exception:
            y = None

        # Example inline reuse (adapt to your code if you have helpers):
        from io import StringIO, BytesIO
        out_dir = os.path.join(current_app.instance_path, "reports")
        os.makedirs(out_dir, exist_ok=True)

        # generate the HTML string the same way as in /api/reports/generate:
        rows = read_csv(y) if y else read_csv(None)      # <- uses your existing helper
        if y and not rows:
            rows = read_csv(None)
        summary = summarize(rows)                         # <- your existing helper
        html_str, fname = build_report_html(rows, summary, y)   # <- factor tiny helper as shown below

        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_str)

        return send_file(path, as_attachment=True, download_name=fname, mimetype="text/html")

    def build_report_html(rows, summary, year=None):
        from datetime import datetime

        # Pick filename like: report_2024_20251106-161045.html
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        tag = str(year) if year else "all"
        fname = f"report_{tag}_{ts}.html"

        # Build a simple HTML document string (reuse your CSS + template parts)
        html_parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            "<meta charset='utf-8'/>",
            f"<title>Report {tag}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 2em; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; }",
            "th { background-color: #f5f5f5; }",
            "</style>",
            "</head><body>",
            f"<h1>Events Report {tag}</h1>",
            f"<p><strong>Total Events:</strong> {summary['total_events']}</p>",
            f"<p><strong>Total Attendance:</strong> {summary['total_attendance']}</p>",
            "<table><thead><tr><th>Title</th><th>Date</th><th>Attendance</th></tr></thead><tbody>"
        ]

        for r in rows:
            html_parts.append(
                f"<tr><td>{r['title']}</td><td>{r['date']}</td><td>{r['attendance']}</td></tr>"
            )

        html_parts.append("</tbody></table></body></html>")

        return "".join(html_parts), fname

    @app.get("/reports/files/<path:filename>")
    def serve_report_file(filename):
        out_dir = os.path.join(app.instance_path, "reports")
        as_download = request.args.get("download") == "1"
        resp = send_from_directory(
            out_dir,
            filename,
            as_attachment=as_download,
            download_name=filename,
            mimetype="text/html",
        )
        if as_download:
            # Some browsers still try to preview text/html; nudge them to download.
            resp.headers["Content-Type"] = "application/octet-stream"
        return resp

    @app.get("/reports")
    def reports_page():
        return render_template("report.html")

    @app.errorhandler(Exception)
    def api_errors(e):
        if request.path.startswith('/api/'):
            # keep it terse; you can add traceback if you want
            return jsonify({"error": str(e)}), 500
        raise e

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)