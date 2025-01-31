import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db, User, ChitFund, Round, Payment, Bid

def upgrade():
    try:
        # Add winning_info column to round table
        db.engine.execute('ALTER TABLE round ADD COLUMN winning_info TEXT')
    except:
        print("winning_info column might already exist in round table")
    
    try:
        # Add total_savings column to user table
        db.engine.execute('ALTER TABLE user ADD COLUMN total_savings FLOAT DEFAULT 0.0')
    except:
        print("total_savings column might already exist in user table")
    
    try:
        # Update total_savings with existing savings values
        db.engine.execute('UPDATE user SET total_savings = savings WHERE total_savings IS NULL')
    except:
        print("Error updating total_savings values")

def downgrade():
    # Remove the new columns
    try:
        db.engine.execute('ALTER TABLE round DROP COLUMN winning_info')
    except:
        print("Error dropping winning_info column")
    
    try:
        db.engine.execute('ALTER TABLE user DROP COLUMN total_savings')
    except:
        print("Error dropping total_savings column")

if __name__ == '__main__':
    # Get the absolute path to the database
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    instance_dir = os.path.join(basedir, 'instance')
    
    # Create instance directory if it doesn't exist
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    db_path = os.path.join(instance_dir, 'chit_fund.db')
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Create all tables first
        db.create_all()
        print("Created all tables")
        
        # Then run the migration
        upgrade()
        print("Migration completed")
