from flask import Flask
from flask_login import LoginManager
from models import db, Events, User
from load_data import load_events
from views import main_blueprint
from auth import auth_blueprint, init_oauth
from report_gen import reports_bp
import os
import json
from dotenv import load_dotenv
load_dotenv()
print("Loaded TABS:", os.getenv("GOOGLE_SHEETS_TABS"))


login_manager = LoginManager()

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'dev'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

    # Google Sheets config
    creds_str = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if creds_str:
        app.config["GOOGLE_SHEETS_CREDENTIALS"] = json.loads(creds_str)
    else:
        app.config["GOOGLE_SHEETS_CREDENTIALS"] = None
    app.config["GOOGLE_SHEETS_SHEET_ID"] = os.environ.get("GOOGLE_SHEETS_SHEET_ID")
    app.config["GOOGLE_SHEETS_TABS"] = os.environ.get("GOOGLE_SHEETS_TABS")
    
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.signIn'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # OAuth
    init_oauth(app)

    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    

    with app.app_context():
        db.create_all()
        if Events.query.count() == 0:
            print("No data found in database - begin loading csv data")
            load_events()
        else:
            print("Data already loaded - skipping csv import")

    # Ensure reports folder exists
    os.makedirs(os.path.join(app.instance_path, "reports"), exist_ok=True)

    return app
