import os
from flask import Flask
from models import db

def reset_database():
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(basedir, 'instance')
    db_path = os.path.join(instance_dir, 'chit_fund.db')
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create Flask app and configure it
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Create all tables
    with app.app_context():
        db.create_all()
        print("Created new database with all tables")

if __name__ == '__main__':
    reset_database()
