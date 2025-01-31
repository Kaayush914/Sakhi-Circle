from app import app
from models import db, User, ChitFund, Round, Payment, Bid, chitfund_members

def clean_database():
    print("\n=== Cleaning Database ===")
    
    with app.app_context():
        try:
            # Get all users before cleaning
            users = User.query.all()
            print(f"Found {len(users)} registered users")
            
            # Delete all bids
            num_bids = Bid.query.delete()
            print(f"Deleted {num_bids} bids")
            
            # Delete all payments
            num_payments = Payment.query.delete()
            print(f"Deleted {num_payments} payments")
            
            # Delete all rounds
            num_rounds = Round.query.delete()
            print(f"Deleted {num_rounds} rounds")
            
            # Delete all chitfund member associations
            db.session.execute(chitfund_members.delete())
            print("Deleted all chitfund member associations")
            
            # Delete all chitfunds
            num_chitfunds = ChitFund.query.delete()
            print(f"Deleted {num_chitfunds} chitfunds")
            
            # Reset user savings to 0
            for user in users:
                user.savings = 0.0
                print(f"Reset savings for user {user.username}")
            
            # Commit all changes
            db.session.commit()
            print("\nDatabase cleaned successfully!")
            print("All registered users preserved with savings reset to 0")
            
        except Exception as e:
            print(f"Error cleaning database: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    clean_database()
