import os
from flask import Flask
from models import db
from datetime import datetime

def rebuild_database():
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(basedir, 'instance')
    db_path = os.path.join(instance_dir, 'chit_fund.db')
    
    # Ensure instance directory exists
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
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
        
        # Verify table structure
        tables = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print("\nCreated tables:")
        for table in tables:
            table_name = table[0]
            columns = db.engine.execute(f"PRAGMA table_info({table_name});").fetchall()
            print(f"\n{table_name} columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")

if __name__ == '__main__':
    rebuild_database()
