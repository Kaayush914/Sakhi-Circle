import sqlite3
import os

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    return any(col[1] == column for col in columns)

def add_columns():
    # Get database path
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'chit_fund.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check and add total_savings column to user table
        if not column_exists(cursor, 'user', 'total_savings'):
            cursor.execute('ALTER TABLE user ADD COLUMN total_savings FLOAT DEFAULT 0.0')
            print("Added total_savings column to user table")
        else:
            print("total_savings column already exists in user table")
        
        # Check and add winning_info column to round table
        if not column_exists(cursor, 'round', 'winning_info'):
            cursor.execute('ALTER TABLE round ADD COLUMN winning_info TEXT')
            print("Added winning_info column to round table")
        else:
            print("winning_info column already exists in round table")
        
        # Update total_savings with existing savings values
        cursor.execute('UPDATE user SET total_savings = savings WHERE total_savings IS NULL')
        print("Updated total_savings values")
        
        # Commit the changes
        conn.commit()
        print("Changes committed successfully")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    add_columns()
