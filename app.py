from flask import Flask
from flask_login import LoginManager
from models import db, Events, User
from load_data import load_events
from views import main_blueprint
from auth import auth_blueprint, init_oauth
import os

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'dev'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
    
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

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
