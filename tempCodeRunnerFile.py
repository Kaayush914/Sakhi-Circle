
            # Delete all payments
            num_payments = Payment.query.delete()
            print(f"Deleted {num_payments} payments")
            
            # Delete all rounds
            num_rounds = Round.query.delete()
            print(f"Deleted {num_rounds} rounds")
            
            # Delete all chitfund member associations
            db.session.execute(chitfund_members