from app import app
from models import db
import os

def reset_database():
    # Get the database file path
    db_path = 'instance/sakhicircle.db'
    
    # Remove existing database file
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create application context
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Created new database with all tables")

if __name__ == '__main__':
    reset_database()
