from app import create_app, db
from models import ChitFund, Payment, Bid, Round

def reset_data():
    app = create_app()
    with app.app_context():
        try:
            # Delete all bids first (child records)
            Bid.query.delete()
            print("Deleted all bids")
            
            # Delete all payments
            Payment.query.delete()
            print("Deleted all payments")
            
            # Delete all rounds
            Round.query.delete()
            print("Deleted all rounds")
            
            # Delete all chit funds
            ChitFund.query.delete()
            print("Deleted all chit funds")
            
            # Reset user savings to 0
            db.session.execute('UPDATE user SET savings = 0')
            print("Reset user savings to 0")
            
            # Commit the changes
            db.session.commit()
            print("Successfully reset all chit fund data while preserving users")
            
        except Exception as e:
            print(f"Error resetting data: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    reset_data()
