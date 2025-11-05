import os
import csv
from models import db, Events
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from load_data import load_events
from views import main_blueprint


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
    
    return app 


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)




# app = Flask(__name__)

# # ------------------------------------------------------------
# # Configuration
# # ------------------------------------------------------------
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'  # or 'postgresql://user:password@localhost/dbname'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db.init_app(app)

# @app.before_request
# def create_tables():
#     db.create_all()

# # ------------------------------------------------------------
# # Route to load events from CSV
# # ------------------------------------------------------------
# @app.route('/')
# def load_events():
#     csv_path = os.path.join(app.root_path, 'SW_Events.csv')

#     if not os.path.exists(csv_path):
#         return f"CSV file not found at {csv_path}", 404

#     with open('SW_Events.csv', newline='', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             # Extract and parse the time range safely
#             time_range = row['Time'].strip()
#             try:
#                 start_str, end_str = [t.strip() for t in time_range.split('-')]
#                 start_time = datetime.strptime(start_str, '%I %p').time()
#                 end_time = datetime.strptime(end_str, '%I %p').time()
#             except ValueError:
#                 print(f"⚠️ Skipping row with invalid time: {time_range}")
#                 continue  # skip bad rows instead of crashing

#             # Now safely create your event object
#             event = Events(
#                 title=row['Name of Event/Activity'],
#                 date=datetime.strptime(row['Date'], '%d-%b-%y').date(),  # adjust format if needed
#                 start_time=start_time,
#                 end_time=end_time,
#                 attendance=int(row['Attendance']) if row['Attendance'] else 0,
#                 location=row['Location'],
#                 description=None,  # optional
#                 advert_id=1,       # placeholder, change as needed
#                 partner_id=None,
#                 lead_organizer=1,  # placeholder, change as needed
#                 type_id=1
#             )
#             db.session.add(event)
#         db.session.commit()
#     return "Events loaded successfully from CSV!"


# # ------------------------------------------------------------
# # Run App
# # ------------------------------------------------------------
# if __name__ == '__main__':
#     os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
#     app.run(debug=True)



# from __future__ import annotations
# import os, io, csv
# from datetime import time as Time
# from flask import Flask, jsonify, request, send_file, abort, render_template
# from models import db, Events 


# def create_app():
#     app = Flask(__name__, template_folder="templates", static_folder="static")
#     os.makedirs(app.instance_path, exist_ok=True) 
#     db_file = os.path.join(app.instance_path, "dev.sqlite")
#     sqlite_uri = "sqlite:///" + db_file  

#     app.config.update(
#         SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
#         SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", sqlite_uri),
#         SQLALCHEMY_TRACK_MODIFICATIONS=False,
#         JSON_SORT_KEYS=False,
#     )

#     db.init_app(app)
#     with app.app_context():
#         db.create_all()

#     register_routes(app)
#     register_cli(app)
#     return app

# def register_routes(app: Flask):
#     # ---- Pages ----
#     @app.get("/")
#     def dashboard():
#         return render_template("dashboard.html")

#     # ---- APIs ----
#     @app.get("/api/events")
#     def list_events():
#         rows = Events.query.order_by(Events.id.asc()).all()
#         def to_json(e: Events):
#             st = e.start_time.strftime("%H:%M") if isinstance(e.start_time, Time) else str(e.start_time)
#             return {"id": e.id, "title": e.title, "start_time": st}
#         return jsonify([to_json(e) for e in rows])

#     @app.get("/api/reports/export.csv")
#     def export_csv():
#         rows = Events.query.order_by(Events.id.asc()).all()
#         buf = io.StringIO()
#         w = csv.writer(buf)
#         w.writerow(["id", "title", "start_time"])
#         for e in rows:
#             st = e.start_time.strftime("%H:%M") if isinstance(e.start_time, Time) else str(e.start_time)
#             w.writerow([e.id, e.title, st])
#         mem = io.BytesIO(buf.getvalue().encode("utf-8"))
#         mem.seek(0)
#         return send_file(mem, as_attachment=True, download_name="events.csv", mimetype="text/csv")

#     # Dev-only seed (local)
#     @app.post("/api/dev/seed")
#     def dev_seed():
#         samples = [
#             ("Welcome Fair", Time(9, 0)),
#             ("Alumni Talk", Time(11, 30)),
#             ("Workshop: Python", Time(14, 0)),
#             ("Networking Eve", Time(17, 30)),
#             ("Seminar: AI", Time(10, 0)),
#         ]
#         for title, st in samples:
#             db.session.add(Events(title=title, start_time=st))
#         db.session.commit()
#         return ("", 204)

# def register_cli(app: Flask):
#     @app.cli.command("seed")
#     def seed_cmd():
#         from datetime import time as T
#         samples = [("Orientation", T(9, 0)), ("Career Fair", T(13, 0)), ("Hackathon", T(18, 0))]
#         for title, st in samples:
#             db.session.add(Events(title=title, start_time=st))
#         db.session.commit()
#         print("Seeded demo events")

# app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True)