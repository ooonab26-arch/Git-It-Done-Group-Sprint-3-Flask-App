from flask import Flask
from models import db, Events
from load_data import load_events
from views import main_blueprint
from auth import auth_blueprint
import os

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

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
