from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from models import db, User, ChitFund, Round, Bid, Payment, chitfund_members
from datetime import datetime
from functools import wraps
import uuid

routes = Blueprint('routes', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@routes.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard'))
    return render_template('index.html')

@routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        mobile_number = request.form.get('mobile_number')
        
        # Basic validation
        if not all([username, password, full_name, mobile_number]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('routes.register'))
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('routes.register'))
        
        # Check if mobile number already exists
        if User.query.filter_by(mobile_number=mobile_number).first():
            flash('Mobile number already registered', 'error')
            return redirect(url_for('routes.register'))
        
        try:
            # Create new user
            user = User(
                username=username,
                full_name=full_name,
                mobile_number=mobile_number
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('routes.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
            return redirect(url_for('routes.register'))
    
    return render_template('register.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Successfully logged in!', 'success')
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@routes.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('routes.login'))

@routes.route('/dashboard')
@login_required
def dashboard():
    try:
        user = get_current_user()
        if not user:
            return redirect(url_for('routes.login'))
        
        # Get all chitfunds where the user is a member
        user_chitfunds = db.session.query(ChitFund).join(
            chitfund_members
        ).filter(
            chitfund_members.c.user_id == user.id
        ).all()
        
        funds_info = []
        for fund in user_chitfunds:
            # Get current round
            current_round = Round.query.filter_by(
                chitfund_id=fund.id,
                round_number=fund.current_round
            ).first()
            
            # Get payment status for current round
            payment = None
            can_bid = False
            total_pooled = 0
            
            if current_round:
                # Calculate total pooled amount from completed payments
                completed_payments = Payment.query.filter_by(
                    chitfund_id=fund.id,
                    round_id=current_round.id,
                    status='completed'
                ).all()
                
                total_pooled = sum(payment.amount for payment in completed_payments)
                
                payment = Payment.query.filter_by(
                    chitfund_id=fund.id,
                    round_id=current_round.id,
                    user_id=user.id
                ).first()
                
                # If no payment record exists, create one
                if not payment and current_round.status != 'completed':
                    payment = Payment(
                        chitfund_id=fund.id,
                        round_id=current_round.id,
                        user_id=user.id,
                        amount=fund.monthly_contribution,
                        status='pending'
                    )
                    db.session.add(payment)
                    db.session.commit()
                
                # Check if user can bid
                if current_round.status == 'bidding' and payment and payment.status == 'completed':
                    # Check if all users have made their payments
                    total_members = fund.member_count
                    completed_payments_count = len(completed_payments)
                    all_payments_made = total_members == completed_payments_count

                    if not all_payments_made:
                        can_bid = False
                    else:
                        # Check if user has already bid
                        existing_bid = Bid.query.filter_by(
                            chitfund_id=fund.id,
                            round_id=current_round.id,
                            user_id=user.id
                        ).first()
                        
                        # Check if user has already won a round
                        previous_wins = Round.query.filter_by(
                            chitfund_id=fund.id,
                            winner_id=user.id,
                            status='completed'
                        ).count()
                        
                        # User can bid if they haven't bid in this round and haven't won before
                        can_bid = not existing_bid and previous_wins == 0
                
                # Get all bids for the current round
                current_round.bids = Bid.query.filter_by(
                    chitfund_id=fund.id,
                    round_id=current_round.id
                ).all()
                
                # Get all payments for the current round
                current_round.payments = Payment.query.filter_by(
                    chitfund_id=fund.id,
                    round_id=current_round.id
                ).all()
                
                # If round is completed, get winner info
                if current_round.status == 'completed' and current_round.winner_id:
                    current_round.winner = User.query.get(current_round.winner_id)
            
            # Get previous completed rounds
            previous_rounds = Round.query.filter(
                Round.chitfund_id == fund.id,
                Round.status == 'completed',
                Round.round_number < fund.current_round
            ).order_by(Round.round_number.desc()).all()
            
            funds_info.append({
                'fund': fund,
                'current_round': current_round,
                'payment': payment,
                'can_bid': can_bid,
                'total_pooled': total_pooled,
                'previous_rounds': previous_rounds
            })
        
        return render_template('dashboard.html', user=user, funds=funds_info)
        
    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while loading the dashboard', 'error')
        return redirect(url_for('routes.index'))

@routes.route('/create-chitfund', methods=['GET', 'POST'])
@login_required
def create_chitfund():
    if request.method == 'GET':
        return render_template('create_chitfund.html')
        
    try:
        print("\n=== Creating Chit Fund ===")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            member_ids = data.get('members', [])
            monthly_contribution = float(data.get('monthly_contribution', 0))
            duration = int(data.get('duration', 0))
        else:
            name = request.form.get('name')
            member_ids = request.form.get('member_ids', '').strip().split(',')
            member_ids = [int(id) for id in member_ids if id.strip()]  # Convert to integers
            monthly_contribution = float(request.form.get('monthly_contribution', 0))
            duration = int(request.form.get('duration', 0))
        
        print(f"Name: {name}")
        print(f"Member IDs: {member_ids}")
        print(f"Monthly Contribution: {monthly_contribution}")
        print(f"Duration: {duration}")
        
        if not all([name, monthly_contribution, duration]):
            error_msg = 'Missing required fields'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('routes.create_chitfund'))
        
        # Add creator to members if not already included
        creator_id = session.get('user_id')
        if creator_id not in member_ids:
            member_ids.append(creator_id)
        
        # Validate member count matches duration
        member_count = len(member_ids)
        if member_count != duration:
            error_msg = f'Number of members ({member_count}) must match duration ({duration})'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('routes.create_chitfund'))
        
        # Create new chit fund
        chitfund = ChitFund(
            name=name,
            creator_id=creator_id,
            member_count=member_count,  # Set the member_count
            monthly_contribution=monthly_contribution,
            duration=duration,
            current_round=1,  # Start with round 1
            start_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.session.add(chitfund)
        db.session.flush()  # Get chitfund.id without committing
        print(f"Created chit fund with ID: {chitfund.id}")
        
        # Add members to chitfund
        for member_id in member_ids:
            stmt = chitfund_members.insert().values(
                chitfund_id=chitfund.id,
                user_id=member_id
            )
            db.session.execute(stmt)
            print(f"Added member {member_id} to chit fund")
        
        # Create first round
        first_round = Round(
            chitfund_id=chitfund.id,
            round_number=1,
            status='bidding',
            start_date=datetime.utcnow()
        )
        db.session.add(first_round)
        db.session.flush()  # Get first_round.id without committing
        print(f"Created first round with ID: {first_round.id}")
        
        # Create payment records for first round
        for member_id in member_ids:
            payment = Payment(
                chitfund_id=chitfund.id,
                round_id=first_round.id,
                user_id=member_id,
                amount=monthly_contribution,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(payment)
            print(f"Created payment record for member {member_id}")
        
        # Commit all changes
        db.session.commit()
        print("Successfully committed all changes")
        
        success_msg = 'Chit fund created successfully!'
        if request.is_json:
            return jsonify({
                'message': success_msg,
                'chitfund_id': chitfund.id,
                'first_round_id': first_round.id,
                'member_count': member_count
            })
        
        flash(success_msg, 'success')
        return redirect(url_for('routes.dashboard'))
        
    except Exception as e:
        print(f"Error creating chit fund: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        
        error_msg = f'Error creating chit fund: {str(e)}'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
            
        flash(error_msg, 'error')
        return redirect(url_for('routes.create_chitfund'))

@routes.route('/search-members')
@login_required
def search_members():
    try:
        query = request.args.get('query', '').strip()
        if len(query) < 3:
            return jsonify([])
        
        print(f"\n=== Searching Members ===")
        print(f"Query: {query}")
        
        # Search for users by username, full name, or mobile number
        # Exclude the current user from results
        users = User.query.filter(
            User.id != session.get('user_id'),  # Exclude current user
            db.or_(  # Use db.or_ instead of or_
                User.username.ilike(f'%{query}%'),
                User.full_name.ilike(f'%{query}%'),
                User.mobile_number.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        print(f"Found {len(users)} users")
        
        result = [{
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'mobile_number': user.mobile_number
        } for user in users]
        
        print(f"Returning results: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error searching members: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@routes.route('/api/place_bid', methods=['POST'])
@login_required
def place_bid():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        chitfund_id = data.get('chitfund_id')
        round_id = data.get('round_id')
        bid_amount = float(data.get('amount'))
        user_id = session.get('user_id')
        
        if not all([chitfund_id, round_id, bid_amount]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        print("\n=== Processing Bid ===")
        print(f"ChitFund ID: {chitfund_id}")
        print(f"Round ID: {round_id}")
        print(f"Bid Amount: Rs.{bid_amount}")
        print(f"User ID: {user_id}")
        
        # Validate bid
        chitfund = ChitFund.query.get(chitfund_id)
        if not chitfund:
            return jsonify({'error': 'Invalid chit fund'}), 400
        
        round = Round.query.get(round_id)
        if not round or round.status != 'bidding':
            return jsonify({'error': 'Round not open for bidding'}), 400
        
        # Get all members in the chit fund using the association table
        total_members = db.session.query(User).join(
            chitfund_members
        ).filter(
            chitfund_members.c.chitfund_id == chitfund_id
        ).count()
        print(f"Total members in chit fund: {total_members}")
        
        # For rounds after first round, get count of members who haven't won yet
        if round.round_number > 1:
            # Get list of users who have already won
            previous_winners = db.session.query(Round.winner_id).filter(
                Round.chitfund_id == chitfund_id,
                Round.status == 'completed'
            ).all()
            previous_winner_ids = [w[0] for w in previous_winners]
            print(f"Previous winners: {previous_winner_ids}")
            
            # Count eligible members (those who haven't won)
            eligible_members = db.session.query(User).join(
                chitfund_members
            ).filter(
                chitfund_members.c.chitfund_id == chitfund_id,
                ~User.id.in_(previous_winner_ids)
            ).count()
            print(f"Eligible members for this round: {eligible_members}")
        else:
            eligible_members = total_members
            print(f"First round - all members eligible: {eligible_members}")
        
        # Calculate current pool amount from all completed payments
        completed_payments = Payment.query.filter_by(
            chitfund_id=chitfund_id,
            round_id=round_id,
            status='completed'
        ).all()
        
        total_pooled = sum(payment.amount for payment in completed_payments)
        if bid_amount >= total_pooled:
            return jsonify({
                'error': f'Bid amount (Rs.{bid_amount:,.2f}) must be less than current pool amount (Rs.{total_pooled:,.2f})'
            }), 400
        
        # Check if user has paid for this round
        payment = Payment.query.filter_by(
            chitfund_id=chitfund_id,
            round_id=round_id,
            user_id=user_id,
            status='completed'
        ).first()
        
        if not payment:
            return jsonify({'error': 'You must pay the monthly contribution before bidding'}), 400
        
        # Check if user has already won a round in this chit fund (skip for first round)
        if round.round_number > 1:
            previous_wins = Round.query.filter_by(
                chitfund_id=chitfund_id,
                winner_id=user_id,
                status='completed'
            ).count()
            
            if previous_wins > 0:
                return jsonify({'error': 'You have already won a round in this chit fund'}), 400
        
        # Check if user has already bid in this round
        existing_bid = Bid.query.filter_by(
            chitfund_id=chitfund_id,
            round_id=round_id,
            user_id=user_id
        ).first()
        
        if existing_bid:
            return jsonify({'error': 'You have already placed a bid in this round'}), 400
        
        # Create new bid
        bid = Bid(
            chitfund_id=chitfund_id,
            round_id=round_id,
            user_id=user_id,
            amount=bid_amount,
            timestamp=datetime.utcnow()
        )
        db.session.add(bid)
        db.session.commit()
        
        # Get counts of paid members and bidders
        paid_members_count = len(completed_payments)
        
        # Count unique bidders after adding the new bid
        unique_bidders = db.session.query(Bid.user_id).filter(
            Bid.chitfund_id == chitfund_id,
            Bid.round_id == round_id,
            ~Bid.user_id.in_(previous_winner_ids) if round.round_number > 1 else True
        ).distinct().count()
        
        print(f"\nTotal members in fund: {total_members}")
        print(f"Eligible members: {eligible_members}")
        print(f"Paid members: {paid_members_count}")
        print(f"Total unique bidders: {unique_bidders}")
        
        # Check if all eligible members have bid
        if unique_bidders == eligible_members:
            print("\nAll eligible members have bid - ending round...")
            success, message = end_round_bidding(round_id)
            if success:
                return jsonify({
                    'message': 'Bid placed successfully and round completed',
                    'round_completed': True,
                    'round_result': message
                })
            else:
                return jsonify({'error': f'Error ending round: {message}'}), 500
        
        return jsonify({
            'message': 'Bid placed successfully',
            'bid_amount': bid_amount,
            'bids_received': unique_bidders,
            'total_expected': eligible_members,
            'paid_members': paid_members_count,
            'round_completed': False,
            'total_pool': total_pooled
        })
        
    except Exception as e:
        print(f"Error in place_bid: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def end_round_bidding(round_id):
    """End the bidding for a round and determine the winner"""
    try:
        print(f"\n=== Ending Round {round_id} Bidding ===")
        
        round = Round.query.get(round_id)
        if not round:
            return False, "Round not found"
        
        if round.status != 'bidding':
            return False, "Round is not in bidding status"
        
        chitfund = ChitFund.query.get(round.chitfund_id)
        if not chitfund:
            return False, "Chit fund not found"
        
        # Get all members in the chit fund
        total_members = db.session.query(User).join(
            chitfund_members
        ).filter(
            chitfund_members.c.chitfund_id == round.chitfund_id
        ).count()
        print(f"Total members in chit fund: {total_members}")
        
        # Get all completed payments for this round
        completed_payments = Payment.query.filter_by(
            chitfund_id=round.chitfund_id,
            round_id=round.id,
            status='completed'
        ).all()
        paid_members = [payment.user_id for payment in completed_payments]
        print(f"Paid members: {paid_members}")
        
        # For rounds after first round, get list of previous winners
        previous_winner_ids = []
        if round.round_number > 1:
            previous_winners = db.session.query(Round.winner_id).filter(
                Round.chitfund_id == round.chitfund_id,
                Round.status == 'completed'
            ).all()
            previous_winner_ids = [w[0] for w in previous_winners]
            print(f"Previous winners: {previous_winner_ids}")
        
        # Get all bids for this round
        bids = Bid.query.filter_by(
            chitfund_id=round.chitfund_id,
            round_id=round.id
        ).all()
        
        # Get unique bidders who are eligible (not previous winners)
        unique_bidders = set()
        for bid in bids:
            if round.round_number == 1 or bid.user_id not in previous_winner_ids:
                unique_bidders.add(bid.user_id)
        print(f"Unique eligible bidders: {unique_bidders}")
        
        # For rounds after first round, we only need bids from non-winners
        if round.round_number > 1:
            eligible_members = set(paid_members) - set(previous_winner_ids)
            print(f"Eligible members for this round: {eligible_members}")
            
            if not unique_bidders.issuperset(eligible_members):
                missing_bidders = eligible_members - unique_bidders
                print(f"Missing bids from eligible members: {missing_bidders}")
                return False, "Not all eligible members have placed their bids"
        else:
            # First round - need bids from all paid members
            if not unique_bidders.issuperset(set(paid_members)):
                missing_bidders = set(paid_members) - unique_bidders
                print(f"Missing bids from paid members: {missing_bidders}")
                return False, "Not all paid members have placed their bids"
        
        # Find the winning bid (lowest bid amount)
        valid_bids = [bid for bid in bids if bid.user_id in unique_bidders]
        if not valid_bids:
            return False, "No valid bids found"
        
        winning_bid = min(valid_bids, key=lambda x: x.amount)
        print(f"\nWinning bid: Rs.{winning_bid.amount} by user {winning_bid.user_id}")
        
        # Calculate total pool and dividend
        total_pool = sum(payment.amount for payment in completed_payments)
        dividend_per_member = (total_pool - winning_bid.amount) / (len(completed_payments) - 1)  # Exclude winner from dividend
        print(f"Total pool: Rs.{total_pool}")
        print(f"Dividend per member: Rs.{dividend_per_member}")
        
        # Update round with winner
        round.status = 'completed'
        round.winner_id = winning_bid.user_id
        round.winning_bid = winning_bid.amount
        round.dividend_per_member = dividend_per_member
        round.end_date = datetime.utcnow()
        
        # Update winner's savings with their winning bid
        winner = User.query.get(winning_bid.user_id)
        if winner:
            winner.savings += winning_bid.amount
            print(f"Updated winner's savings: Rs.{winner.savings}")
        
        # Update all other members' savings with their dividend
        for payment in completed_payments:
            if payment.user_id != winning_bid.user_id:  # Skip winner
                user = User.query.get(payment.user_id)
                if user:
                    user.savings += dividend_per_member
                    print(f"Updated {user.username}'s savings with dividend: Rs.{dividend_per_member}")
        
        # Update chitfund current round
        chitfund.current_round = round.round_number
        
        # If this is not the last round, create next round
        if round.round_number < chitfund.duration:
            next_round = Round(
                chitfund_id=round.chitfund_id,
                round_number=round.round_number + 1,
                status='bidding',
                start_date=datetime.utcnow()
            )
            db.session.add(next_round)
            
            # Update chitfund's current round
            chitfund.current_round = next_round.round_number
            
            # Commit to get the next_round.id
            db.session.commit()
            print(f"\nCreated round {next_round.round_number}")
            
            # Now create pending payments for next round
            print("Creating pending payments for next round...")
            for member_id in paid_members:
                payment = Payment(
                    chitfund_id=round.chitfund_id,
                    round_id=next_round.id,
                    user_id=member_id,
                    amount=round.chitfund.monthly_contribution,
                    status='pending',
                    created_at=datetime.utcnow()
                )
                db.session.add(payment)
                print(f"Created pending payment for user {member_id}")
            
            # Commit the payments
            db.session.commit()
            print("All pending payments created successfully")
            print(f"Chit fund current round updated to {chitfund.current_round}")
        else:
            # Just commit the round completion
            db.session.commit()
            print("Final round completed")
        
        return True, {
            'winner_id': winning_bid.user_id,
            'winning_bid': winning_bid.amount,
            'total_pool': total_pool,
            'dividend_per_member': dividend_per_member,
            'next_round': round.round_number + 1 if round.round_number < chitfund.duration else None
        }
        
    except Exception as e:
        print(f"Error ending round: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False, str(e)

@routes.route('/api/make_payment', methods=['POST'])
@login_required
def make_payment():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        chitfund_id = data.get('chitfund_id')
        round_id = data.get('round_id')
        user_id = session.get('user_id')
        
        if not all([chitfund_id, round_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get the chitfund and round
        chitfund = ChitFund.query.get(chitfund_id)
        current_round = Round.query.get(round_id)
        
        if not chitfund or not current_round:
            return jsonify({'error': 'Invalid chitfund or round'}), 400
            
        if current_round.status == 'completed':
            return jsonify({'error': 'This round is already completed'}), 400
        
        # Create or update payment
        payment = Payment.query.filter_by(
            chitfund_id=chitfund_id,
            round_id=round_id,
            user_id=user_id
        ).first()
        
        if not payment:
            payment = Payment(
                chitfund_id=chitfund_id,
                round_id=round_id,
                user_id=user_id,
                amount=chitfund.monthly_contribution,
                status='completed',
                timestamp=datetime.utcnow()
            )
            db.session.add(payment)
        else:
            payment.status = 'completed'
            payment.timestamp = datetime.utcnow()
        
        db.session.commit()

        # Check if this is the last round and all payments are complete
        if current_round.round_number == chitfund.duration:
            # Count completed payments for this round
            completed_payments = Payment.query.filter_by(
                chitfund_id=chitfund_id,
                round_id=round_id,
                status='completed'
            ).count()

            # Get total members in the chitfund
            total_members = db.session.query(User).join(
                chitfund_members
            ).filter(
                chitfund_members.c.chitfund_id == chitfund_id
            ).count()

            # If all members have paid in the last round
            if completed_payments == total_members:
                # Find the user who hasn't won yet
                previous_winners = db.session.query(Round.winner_id).filter(
                    Round.chitfund_id == chitfund_id,
                    Round.status == 'completed'
                ).all()
                previous_winner_ids = [w[0] for w in previous_winners]

                last_user = db.session.query(User).join(
                    chitfund_members
                ).filter(
                    chitfund_members.c.chitfund_id == chitfund_id,
                    ~User.id.in_(previous_winner_ids)
                ).first()

                if last_user:
                    # Calculate total pool amount
                    total_pool = completed_payments * chitfund.monthly_contribution
                    
                    # Update round with winner
                    current_round.winner_id = last_user.id
                    current_round.winning_bid = 0  # No bid for last round
                    current_round.status = 'completed'
                    current_round.dividend_per_member = 0  # No dividend in last round
                    
                    # Update user's savings
                    last_user.savings = (last_user.savings or 0) + total_pool
                    
                    db.session.commit()
                    
                    return jsonify({
                        'message': 'Payment successful and round completed automatically'
                    })

        # Check if all members have paid for regular rounds
        total_paid = Payment.query.filter_by(
            chitfund_id=chitfund_id,
            round_id=round_id,
            status='completed'
        ).count()
        
        if total_paid == chitfund.member_count and current_round.round_number < chitfund.duration:
            current_round.status = 'bidding'
            db.session.commit()
        
        return jsonify({'message': 'Payment successful'})
        
    except Exception as e:
        print(f"Error in make_payment: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Template context processor to get payment status
@routes.app_template_global()
def get_payment_status(chitfund_id, round_number, user_id):
    return Payment.query.filter_by(
        chitfund_id=chitfund_id,
        round_id=Round.query.filter_by(chitfund_id=chitfund_id, round_number=round_number).first().id,  # Use round_id instead of round_number
        user_id=user_id
    ).first()
