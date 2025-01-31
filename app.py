from flask import Flask, session
from models import db
import os
from routes import routes
from datetime import timedelta

app = Flask(__name__)

# Create instance directory if it doesn't exist
if not os.path.exists('instance'):
    os.makedirs('instance')

# Configuration
app.config.update(
    SECRET_KEY='dev',
    SQLALCHEMY_DATABASE_URI='sqlite:///instance/chit_fund.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_NAME='chit_fund_session',
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)

# Initialize extensions
db.init_app(app)

# Register blueprints
app.register_blueprint(routes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
