from app import app
from models import db, User, ChitFund, Round, Payment, Bid
from tabulate import tabulate
from datetime import datetime

def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else 'N/A'

def format_money(amount):
    return f"Rs.{amount:,.2f}" if amount is not None else 'Rs.0.00'

def view_users():
    users = User.query.all()
    if not users:
        print("No users found")
        return
    
    data = []
    for user in users:
        data.append([
            user.id,
            user.username,
            user.full_name,
            user.mobile_number,
            format_datetime(user.created_at),
            format_money(user.savings),
            len(user.created_funds),
            len(user.member_funds)
        ])
    
    headers = ['ID', 'Username', 'Full Name', 'Mobile', 'Created At', 'Savings', 'Created Funds', 'Member Of']
    print("\n=== Users ===")
    print(tabulate(data, headers=headers, tablefmt='grid'))

def view_chitfunds():
    chitfunds = ChitFund.query.all()
    if not chitfunds:
        print("No chit funds found")
        return
    
    data = []
    for cf in chitfunds:
        creator = User.query.get(cf.creator_id)
        members = list(cf.members)
        member_names = [m.username for m in members]
        data.append([
            cf.id,
            cf.name,
            creator.username if creator else 'N/A',
            cf.member_count,
            format_money(cf.monthly_contribution),
            cf.duration,
            cf.current_round,
            format_datetime(cf.start_date),
            format_datetime(cf.created_at),
            len(members),
            ', '.join(member_names)
        ])
    
    headers = ['ID', 'Name', 'Creator', 'Member Count', 'Monthly Contribution', 'Duration', 
              'Current Round', 'Start Date', 'Created At', 'Actual Members', 'Member List']
    print("\n=== Chit Funds ===")
    print(tabulate(data, headers=headers, tablefmt='grid'))

def view_rounds():
    rounds = Round.query.all()
    if not rounds:
        print("No rounds found")
        return
    
    data = []
    for r in rounds:
        chitfund = ChitFund.query.get(r.chitfund_id)
        winner = User.query.get(r.winner_id) if r.winner_id else None
        
        # Get payment and bid counts
        payment_count = Payment.query.filter_by(
            chitfund_id=r.chitfund_id,
            round_id=r.id,
            status='completed'
        ).count()
        
        bid_count = Bid.query.filter_by(
            chitfund_id=r.chitfund_id,
            round_id=r.id
        ).count()
        
        data.append([
            r.id,
            chitfund.name if chitfund else 'N/A',
            r.round_number,
            r.status,
            format_datetime(r.start_date),
            format_datetime(r.end_date),
            winner.username if winner else 'N/A',
            format_money(r.winning_bid),
            format_money(r.dividend_per_member),
            payment_count,
            bid_count
        ])
    
    headers = [
        'ID', 'ChitFund', 'Round#', 'Status', 'Start Date', 'End Date', 
        'Winner', 'Winning Bid', 'Dividend/Member', 'Payments', 'Bids'
    ]
    print("\n=== Rounds ===")
    print(tabulate(data, headers=headers, tablefmt='grid'))

def view_payments():
    payments = Payment.query.all()
    if not payments:
        print("No payments found")
        return
    
    data = []
    for p in payments:
        user = User.query.get(p.user_id)
        round = Round.query.get(p.round_id)
        data.append([
            p.id,
            p.chitfund_id,
            round.round_number if round else 'N/A',
            user.username if user else 'N/A',
            format_money(p.amount),
            p.status,
            p.payment_method or 'N/A',
            p.transaction_id or 'N/A',
            format_datetime(p.payment_date),
            format_datetime(p.created_at)
        ])
    
    headers = ['ID', 'ChitFund ID', 'Round #', 'User', 'Amount', 'Status', 
              'Method', 'Transaction ID', 'Payment Date', 'Created At']
    print("\n=== Payments ===")
    print(tabulate(data, headers=headers, tablefmt='grid'))

def view_bids():
    bids = Bid.query.all()
    if not bids:
        print("No bids found")
        return
    
    data = []
    for b in bids:
        user = User.query.get(b.user_id)
        round = Round.query.get(b.round_id)
        data.append([
            b.id,
            b.chitfund_id,
            round.round_number if round else 'N/A',
            user.username if user else 'N/A',
            format_money(b.amount),
            format_datetime(b.timestamp)
        ])
    
    headers = ['ID', 'ChitFund ID', 'Round #', 'User', 'Amount', 'Timestamp']
    print("\n=== Bids ===")
    print(tabulate(data, headers=headers, tablefmt='grid'))

def view_all():
    with app.app_context():
        print("\nDatabase Contents:")
        print("=" * 80)
        view_users()
        print("\n" + "=" * 80)
        view_chitfunds()
        print("\n" + "=" * 80)
        view_rounds()
        print("\n" + "=" * 80)
        view_payments()
        print("\n" + "=" * 80)
        view_bids()

if __name__ == '__main__':
    view_all()
