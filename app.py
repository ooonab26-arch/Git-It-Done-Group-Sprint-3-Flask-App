from flask import Flask
import cloudinary
import cloudinary.uploader
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

def create_app(testing = False):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'dev'
    db_url = os.environ.get('DATABASE_URL')

    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    if not db_url:
        print("\nWARNING: DATABASE_URL not found — using SQLite locally\n")
        db_url = "sqlite:///events.db"

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url


    # Google Sheets config
    creds_str = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if creds_str:
        app.config["GOOGLE_SHEETS_CREDENTIALS"] = json.loads(creds_str)
    else:
        app.config["GOOGLE_SHEETS_CREDENTIALS"] = None    
    app.config["GOOGLE_SHEETS_SHEET_ID"] = os.environ.get("GOOGLE_SHEETS_SHEET_ID")
    app.config["GOOGLE_SHEETS_TABS"] = os.environ.get("GOOGLE_SHEETS_TABS")
    
    # Cloudinary config
    cloudinary.config(
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
        cloud_key = os.getenv('CLOUDINARY_API_KEY'),
        cloud_secret = os.getenv('CLOUDINARY_API_SECRET')
    )
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.signIn'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # OAuth
    app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")
    init_oauth(app)

    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    

    with app.app_context():
        db.create_all()
        if Events.query.count() == 0:
            if not testing:
                load_events()
        else:
            print("Data already loaded - skipping csv import")

    # Ensure reports folder exists
    os.makedirs(os.path.join(app.instance_path, "reports"), exist_ok=True)
    print("GOOGLE_CLIENT_SECRET:", os.getenv("GOOGLE_CLIENT_SECRET"))

    return app