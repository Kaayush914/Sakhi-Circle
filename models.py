from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association table for ChitFund members
chitfund_members = db.Table('chitfund_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('chitfund_id', db.Integer, db.ForeignKey('chit_fund.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    savings = db.Column(db.Float, default=0.0)  # User's total savings from chit funds
    
    # Relationships
    created_funds = db.relationship('ChitFund', backref='creator', lazy=True, foreign_keys='ChitFund.creator_id')
    member_funds = db.relationship('ChitFund', secondary=chitfund_members, backref=db.backref('members', lazy=True))
    payments = db.relationship('Payment', backref='user', lazy=True)
    bids = db.relationship('Bid', backref='user', lazy=True)
    
    @property
    def total_savings(self):
        """Calculate total savings including dividends"""
        return self.savings if self.savings is not None else 0.0
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ChitFund(db.Model):
    __tablename__ = 'chit_fund'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    member_count = db.Column(db.Integer, nullable=False)
    monthly_contribution = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Number of months
    current_round = db.Column(db.Integer, default=1)
    commission_rate = db.Column(db.Float, default=0.05)  # 5% commission for organizer
    start_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rounds = db.relationship('Round', backref='chitfund', lazy=True)
    payments = db.relationship('Payment', backref='chitfund', lazy=True)
    bids = db.relationship('Bid', backref='chitfund', lazy=True)
    
    @property
    def total_pool_amount(self):
        """Calculate total pool amount for each round"""
        return self.monthly_contribution * self.member_count
    
    @property
    def commission_amount(self):
        """Calculate commission amount for each round"""
        return self.total_pool_amount * self.commission_rate
    
    def __repr__(self):
        return f'<ChitFund {self.name}>'

class Round(db.Model):
    __tablename__ = 'round'
    
    id = db.Column(db.Integer, primary_key=True)
    chitfund_id = db.Column(db.Integer, db.ForeignKey('chit_fund.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, bidding, completed
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    winning_bid = db.Column(db.Float)  # Amount the winner will receive
    dividend_per_member = db.Column(db.Float)  # Amount each non-winner member receives
    
    # Relationships
    winner = db.relationship('User', foreign_keys=[winner_id])
    bids = db.relationship('Bid', backref='round', lazy=True)
    payments = db.relationship('Payment', backref='round', lazy=True)
    
    @property
    def winning_info(self):
        """Get winning information as a dictionary"""
        if not self.winner_id or not self.winning_bid:
            return None
        
        return {
            'user_id': self.winner_id,
            'username': self.winner.username if self.winner else None,
            'bid_amount': self.winning_bid,
            'round_number': self.round_number,
            'total_pool': self.chitfund.monthly_contribution * self.chitfund.member_count if self.chitfund else None,
            'dividend_per_member': self.dividend_per_member
        }
    
    def start_bidding(self):
        """Start bidding for this round"""
        self.status = 'bidding'
        self.start_date = datetime.utcnow()
        db.session.commit()
    
    def end_bidding(self, winner_id, winning_bid):
        """End bidding and calculate dividends"""
        chitfund = self.chitfund
        self.winner_id = winner_id
        self.winning_bid = winning_bid
        
        # Calculate dividend
        savings = chitfund.total_pool_amount - winning_bid - chitfund.commission_amount
        self.dividend_per_member = savings / (chitfund.member_count - 1)  # Exclude winner
        
        # Update winner's savings
        winner = User.query.get(winner_id)
        winner.savings += winning_bid
        
        # Update other members' savings
        for member in chitfund.members:
            if member.id != winner_id:
                member.savings += self.dividend_per_member
        
        self.status = 'completed'
        self.end_date = datetime.utcnow()
        db.session.commit()

class Bid(db.Model):
    __tablename__ = 'bid'
    
    id = db.Column(db.Integer, primary_key=True)
    chitfund_id = db.Column(db.Integer, db.ForeignKey('chit_fund.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Amount user is willing to take
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Bid {self.amount} by User {self.user_id}>'

class Payment(db.Model):
    __tablename__ = 'payment'
    
    id = db.Column(db.Integer, primary_key=True)
    chitfund_id = db.Column(db.Integer, db.ForeignKey('chit_fund.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20))  # upi, bank_transfer, cash
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, completed
    payment_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def complete_payment(self):
        """Mark payment as completed"""
        self.status = 'completed'
        self.payment_date = datetime.utcnow()
        db.session.commit()
