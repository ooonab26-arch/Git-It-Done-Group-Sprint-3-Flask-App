from __future__ import annotations
import os, io, csv
from datetime import time as Time
from flask import Flask, jsonify, request, send_file, abort, render_template
from models import db, Events 

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    os.makedirs("instance", exist_ok=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///instance/dev.sqlite"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
    )

    db.init_app(app)
    with app.app_context():
        db.create_all()

    register_routes(app)
    register_cli(app)
    return app

def register_routes(app: Flask):
    # ---- Pages ----
    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    # ---- APIs ----
    @app.get("/api/events")
    def list_events():
        rows = Events.query.order_by(Events.id.asc()).all()
        def to_json(e: Events):
            st = e.start_time.strftime("%H:%M") if isinstance(e.start_time, Time) else str(e.start_time)
            return {"id": e.id, "title": e.title, "start_time": st}
        return jsonify([to_json(e) for e in rows])

    @app.get("/api/reports/export.csv")
    def export_csv():
        rows = Events.query.order_by(Events.id.asc()).all()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "title", "start_time"])
        for e in rows:
            st = e.start_time.strftime("%H:%M") if isinstance(e.start_time, Time) else str(e.start_time)
            w.writerow([e.id, e.title, st])
        mem = io.BytesIO(buf.getvalue().encode("utf-8"))
        mem.seek(0)
        return send_file(mem, as_attachment=True, download_name="events.csv", mimetype="text/csv")

    # Dev-only seed (local)
    @app.post("/api/dev/seed")
    def dev_seed():
        samples = [
            ("Welcome Fair", Time(9, 0)),
            ("Alumni Talk", Time(11, 30)),
            ("Workshop: Python", Time(14, 0)),
            ("Networking Eve", Time(17, 30)),
            ("Seminar: AI", Time(10, 0)),
        ]
        for title, st in samples:
            db.session.add(Events(title=title, start_time=st))
        db.session.commit()
        return ("", 204)

def register_cli(app: Flask):
    @app.cli.command("seed")
    def seed_cmd():
        from datetime import time as T
        samples = [("Orientation", T(9, 0)), ("Career Fair", T(13, 0)), ("Hackathon", T(18, 0))]
        for title, st in samples:
            db.session.add(Events(title=title, start_time=st))
        db.session.commit()
        print("Seeded demo events")

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)