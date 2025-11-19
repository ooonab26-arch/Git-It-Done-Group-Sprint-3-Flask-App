from flask import jsonify, request
from models import db, Events
from flask import Flask, jsonify, request, send_file, send_from_directory, render_template, current_app
from flask_sqlalchemy import SQLAlchemy
from load_data import load_events
from views import main_blueprint
from werkzeug.exceptions import HTTPException, NotFound
import os
import io
import csv
from datetime import datetime
import json
import calendar

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
            rows = read_csv(year=None)
            fallback_used = True

        summary = summarize(rows)

        # Title and note
        title = f"Events Report {year}" if year and not fallback_used else "Events Report (All Years)"
        note = "" if (year and not fallback_used) else (
            f"<p style='color:#6b7280'>No rows found for {year}. Showing all years.</p>" if year else ""
        )

        # Prepare chart data
        by_month = summary['by_month']
        js_month_labels = list(by_month.keys())
        js_events_series = [by_month[m]['events'] for m in js_month_labels]
        js_att_series = [by_month[m]['attendance'] for m in js_month_labels]

        # Fake pie chart grouping by event type
        type_counts = {}
        for r in rows:
            t = r.get('type', 'Unknown') or 'Unknown'
            type_counts[t] = type_counts.get(t, 0) + 1

        js_pie_labels = list(type_counts.keys())
        js_pie_values = list(type_counts.values())

        # HTML layout
        html = [
            "<!doctype html><meta charset='utf-8'><title>Events Report</title>",
            """<style>
            body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:24px}
            .card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:12px 0}
            .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
            .chart-350{position:relative;height:350px;}
            .chart-350>canvas{width:100%!important;height:100%!important;display:block}
            table{border-collapse:collapse;width:100%}
            th,td{border:1px solid #e5e7eb;padding:8px;text-align:left}
            th{background:#f8fafc}
            </style>""",
            f"<h1>{title}</h1>",
            note,
            f"<div class='card'><b>Total Events:</b> {summary['total_events']}<br><b>Total Attendees:</b> {summary['total_attendees']}</div>",
            "<div class='grid'>"
            "  <div class='card'>"
            "    <h3 style='margin-top:0'>Events by Month</h3>"
            "    <div class='chart-350'><canvas id='lineChart'></canvas></div>"
            "  </div>"
            "  <div class='card'>"
            "    <h3 style='margin-top:0'>Events by Type</h3>"
            "    <div class='chart-350'><canvas id='pieChart'></canvas></div>"
            "  </div>"
            "</div>",
        ]

        # Event table
        html.append("<div class='card'><h3>Events</h3><table><thead><tr><th>Title</th><th>Date</th><th>Start</th><th>End</th><th>Attendance</th><th>Location</th><th>Type</th></tr></thead><tbody>")
        for r in rows[:100]:
            d = r['date'].isoformat() if r['date'] else ''
            html.append(
                f"<tr><td>{r['title']}</td><td>{d}</td><td>{r['start_time']}</td><td>{r['end_time']}</td><td>{r['attendance']}</td><td>{r['location']}</td><td>{r['type']}</td></tr>"
            )
        html.append("</tbody></table></div>")

        # Chart.js initialization
        html.append(
            "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>"
            "<script>(function(){"
            f"const monthLabels={js_month_labels};"
            f"const eventsSeries={js_events_series};"
            f"const pieLabels={js_pie_labels};"
            f"const pieValues={js_pie_values};"

            "new Chart(document.getElementById('lineChart'), {"
            "  type:'line',"
            "  data:{ labels:monthLabels, datasets:[{ label:'Events', data:eventsSeries, fill:false, borderColor:'#3B82F6', tension:0.2 }] },"
            "  options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:true} }, scales:{ y:{ beginAtZero:true, ticks:{precision:0} } } }"
            "});"

            "new Chart(document.getElementById('pieChart'), {"
            "  type:'pie',"
            "  data:{ labels:pieLabels, datasets:[{ data:pieValues, backgroundColor:['#3B82F6','#10B981','#F59E0B','#EF4444','#6366F1','#EC4899'] }] },"
            "  options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{ position:'bottom' } } }"
            "});"

            "})();</script>"
        )

        html = ''.join(html)

        # Save report
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        fname = f"report_{year if year else 'all'}_{ts}.html"
        out_dir = os.path.join(app.instance_path, 'reports')
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as fp:
            fp.write(html)

        return jsonify({"report_id": fname, "url": f"/reports/files/{fname}", "format": "html"})

    @app.get("/api/events/years")
    def events_years():
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
        rows = read_csv(y) if y else read_csv(
            None)      # <- uses your existing helper
        if y and not rows:
            rows = read_csv(None)
        # <- your existing helper
        summary = summarize(rows)
        # <- factor tiny helper as shown below
        html_str, fname = build_report_html(rows, summary, y)

        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_str)

        return send_file(path, as_attachment=True, download_name=fname, mimetype="text/html")

    def _coerce_date(s: str):
        if not s:
            return None
        s = s.strip()
        # Try ISO first
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            pass
        # Try 25-Jan-25
        try:
            return datetime.strptime(s, "%d-%b-%y").date()
        except Exception:
            return None

    def build_report_html(rows, summary, year=None):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        tag = str(year) if year else "all"
        fname = f"report_{tag}_{ts}.html"

        # ---- Build series for charts ----
        # Normalize and aggregate
        monthly_counts = {m: 0 for m in range(1, 13)}   # events per month
        type_counts = {}                                 # pie by event type

        for r in rows or []:
            # Date
            d = _coerce_date(r.get("date") or r.get("Date"))
            if d:
                monthly_counts[d.month] = monthly_counts.get(d.month, 0) + 1

            # Type
            t = (r.get("type") or r.get("Type") or "").strip()
            if t:
                type_counts[t] = type_counts.get(t, 0) + 1

        # Prepare chart arrays
        line_labels = [calendar.month_abbr[m] for m in range(1, 13)]
        line_data_events = [monthly_counts.get(m, 0) for m in range(1, 13)]

        pie_labels = list(type_counts.keys()) or ["No type data"]
        pie_data = list(type_counts.values()) or [
            summary.get("total_events", 0)]

        # ---- Compose HTML ----
        total_events = summary.get("total_events", 0)
        total_attendance = summary.get("total_attendance", 0)

        # JSON for Chart.js
        jl = json.dumps(line_labels)
        jd_events = json.dumps(line_data_events)
        jp_labels = json.dumps(pie_labels)
        jp_data = json.dumps(pie_data)

        title_text = f"Events Report ({'All Years' if not year else year})"

        html = f"""<!doctype html>
        <html>
        <head>
        <meta charset="utf-8" />
        <title>{title_text}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            :root {{ --card:#ffffff; --muted:#f2f4f7; --text:#111827; --sub:#6b7280; }}
            body {{ font-family: -apple-system, Segoe UI, Roboto, Inter, system-ui, sans-serif; background:#fff; color:var(--text); margin:24px; }}
            .wrap {{ max-width: 1100px; margin: 0 auto; }}
            h1 {{ margin: 0 0 12px 0; }}
            .pill {{ display:inline-block; background:var(--muted); padding:4px 10px; border-radius:999px; font-size:12px; }}
            .grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:16px; }}
            .card {{ background:var(--card); border:1px solid #e5e7eb; border-radius:12px; padding:16px; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
            .kpis {{ display:flex; gap:12px; margin-bottom:16px; }}
            .kpi {{ background:var(--card); border:1px solid #e5e7eb; border-radius:12px; padding:12px 14px; }}
            table {{ width:100%; border-collapse: collapse; }}
            th, td {{ padding:10px; border-bottom:1px solid #eef2f7; text-align:left; }}
            th {{ background:#f8fafc; }}
            .mt16 {{ margin-top:16px; }}
            .mt24 {{ margin-top:24px; }}
        </style>
        </head>
        <body>
        <div class="wrap">
        <h1>{title_text}</h1>
        <div class="kpis">
            <div class="kpi"><div class="pill">Total Events</div><div style="font-size:28px; font-weight:700;">{total_events}</div></div>
            <div class="kpi"><div class="pill">Total Attendees</div><div style="font-size:28px; font-weight:700;">{total_attendance}</div></div>
        </div>

        <div class="grid mt16">
            <div class="card">
            <h3 style="margin:0 0 10px 0;">Events by Month</h3>
            <canvas id="lineChart" height="140"></canvas>
            </div>
            <div class="card">
            <h3 style="margin:0 0 10px 0;">Events by Type</h3>
            <canvas id="pieChart" height="140"></canvas>
            </div>
        </div>

        <div class="card mt24">
            <h3 style="margin:0 0 10px 0;">Events</h3>
            <table>
            <thead>
                <tr>
                <th>Title</th><th>Date</th><th>Start</th><th>End</th><th>Attendance</th><th>Location</th><th>Type</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td>{(r.get('title') or r.get('Title') or '').strip()}</td>"
                         f"<td>{(r.get('date') or r.get('Date') or '').strip()}</td>"
                         f"<td>{(r.get('start') or r.get('Start') or '').strip()}</td>"
                         f"<td>{(r.get('end') or r.get('End') or '').strip()}</td>"
                         f"<td>{(r.get('attendance') or r.get('Attendance') or 0)}</td>"
                         f"<td>{(r.get('location') or r.get('Location') or '').strip()}</td>"
                         f"<td>{(r.get('type') or r.get('Type') or '').strip()}</td></tr>"
                         for r in (rows or []))}
            </tbody>
            </table>
        </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        (function() {{
        // Data embedded from Python
        const lineLabels = {jl};
        const eventsPerMonth = {jd_events};
        const pieLabels = {jp_labels};
        const pieData = {jp_data};

        // Line chart (events per month)
        new Chart(document.getElementById('lineChart'), {{
            type: 'line',
            data: {{
            labels: lineLabels,
            datasets: [{{
                label: 'Events',
                data: eventsPerMonth,
                fill: false
            }}]
            }},
            options: {{
            responsive: true,
            plugins: {{
                legend: {{ display: true }}
            }},
            scales: {{
                y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }}
            }}
            }}
        }});

        // Pie chart (by type)
        new Chart(document.getElementById('pieChart'), {{
            type: 'pie',
            data: {{
            labels: pieLabels,
            datasets: [{{
                data: pieData
            }}]
            }},
            options: {{
            responsive: true,
            plugins: {{
                legend: {{ position: 'bottom' }}
            }}
            }}
        }});
        }})();
        </script>
        </body>
        </html>"""

        return html, fname

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

    @app.route("/events")
    def events():
        return render_template("event.html")

    @app.errorhandler(Exception)
    def api_errors(e):
        # If it's a normal Flask/Werkzeug HTTP error (like 404), return it as-is.
        if isinstance(e, HTTPException):
            # Special-case favicon 404 to reduce log noise (optional)
            if isinstance(e, NotFound) and request.path == "/favicon.ico":
                return ("", 204)  # no content, no error in logs
            return e

        # Otherwise it's a real server error. Log it and return JSON 500.
        current_app.logger.exception(e)
        return jsonify(error="Internal Server Error"), 500


    return app

# link to different documents
@main_blueprint.route("/")
def home():
    events = Events.query.all()
    return render_template("dashboard.html", events=events)

@main_blueprint.route("/report")
def report():
    return render_template("report.html")

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
