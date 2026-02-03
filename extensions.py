from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialized here, bound to the Flask app in app.py with init_app
db = SQLAlchemy()
migrate = Migrate()
