from flask import Flask, session
from models import db
import os
from routes import routes
from datetime import timedelta
from dotenv import load_dotenv
import urllib.parse
import pymysql
pymysql.install_as_MySQLdb()

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Create instance directory if it doesn't exist
if not os.path.exists('instance'):
    os.makedirs('instance')

# MySQL Configuration - URL encode the password to handle special characters
password = urllib.parse.quote_plus('Sonu2004@')
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://Kaayush914:{password}@localhost/chit_fund'

# Configuration
app.config.update(
    SECRET_KEY='dev',
    SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
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
    app.run(debug=True)
