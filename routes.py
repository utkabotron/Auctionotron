import os
import json
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import desc, or_
from app import app, db
from models import User, Listing, ListingPhoto, Bid, SaleMode, ListingStatus
from utils import (
    verify_telegram_webapp_data, 
    parse_telegram_user_data, 
    process_uploaded_image,
    format_price,
    calculate_time_remaining
)

@app.route('/')
def index():
    """Main page - Home screen"""
    user_id = session.get('user_id')
    
    # For development - create test user if none exists
    if not user_id:
        test_user = User.query.filter_by(telegram_id=12345).first()
        if not test_user:
            test_user = User(
                telegram_id=12345,
                first_name='Тестовый пользователь',
                username='testuser'
            )
            db.session.add(test_user)
            db.session.commit()
        session['user_id'] = test_user.id
        user_id = test_user.id
    
    current_user = User.query.get(user_id) if user_id else None
    user_listings = []
    
    if user_id:
        user_listings = Listing.query.filter_by(
            seller_id=user_id
        ).filter(
            Listing.status.in_([ListingStatus.ACTIVE, ListingStatus.ENDED])
        ).order_by(desc(Listing.created_at)).limit(5).all()
    
    return render_template('index.html', user_listings=user_listings, current_user=current_user)

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """Authenticate user via Telegram WebApp"""
    try:
        data = request.get_json()
        init_data = data.get('initData')
        
        if not init_data:
            return jsonify({'error': 'No init data provided'}), 400
        
        # Get bot token from environment
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            app.logger.error('TELEGRAM_BOT_TOKEN not set')
            return jsonify({'error': 'Server configuration error'}), 500
        
        # Verify the data (in production, uncomment this)
        # if not verify_telegram_webapp_data(init_data, bot_token):
        #     return jsonify({'error': 'Invalid authentication data'}), 401
        
        # Parse user data
        user_data = parse_telegram_user_data(init_data)
        if not user_data:
            return jsonify({'error': 'Could not parse user data'}), 400
        
        # Find or create user
        user = User.query.filter_by(telegram_id=user_data['id']).first()
        if not user:
            user = User(
                telegram_id=user_data['id'],
                username=user_data.get('username'),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name')
            )
            db.session.add(user)
            db.session.commit()
        
        # Store user in session
        session['user_id'] = user.id
        session['telegram_id'] = user.telegram_id
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'telegram_id': user.telegram_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
        
    except Exception as e:
        app.logger.error(f"Authentication error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/create')
def create_listing():
    """Create listing wizard"""
    # For development, allow access without authentication
    # In production, you would uncomment the authentication check
    # if 'user_id' not in session:
    #     return redirect(url_for('index'))
    return render_template('create_listing.html')

@app.route('/my-listings')
def my_listings():
    """User's listings management"""
    # For development, allow access without authentication
    # if 'user_id' not in session:
    #     return redirect(url_for('index'))
    
    user_id = session.get('user_id', 1)  # Default to user 1 for development
    status_filter = request.args.get('status', 'all')
    
    query = Listing.query.filter_by(seller_id=user_id)
    
    if status_filter == 'active':
        query = query.filter_by(status=ListingStatus.ACTIVE)
    elif status_filter == 'ended':
        query = query.filter(Listing.status.in_([ListingStatus.ENDED, ListingStatus.SOLD, ListingStatus.CLOSED]))
    elif status_filter == 'draft':
        query = query.filter_by(status=ListingStatus.DRAFT)
    
    listings = query.order_by(desc(Listing.created_at)).all()
    
    return render_template('my_listings.html', listings=listings, status_filter=status_filter)

@app.route('/api/listings', methods=['POST'])
def create_listing_api():
    """Create a new listing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    try:
        data = request.get_json()
        
        # Create new listing
        listing = Listing(
            title=data['title'],
            description=data.get('description', ''),
            category=data.get('category'),
            condition=data.get('condition'),
            sale_mode=SaleMode(data['sale_mode']),
            seller_id=user_id
        )
        
        # Set mode-specific fields
        if listing.sale_mode == SaleMode.FIXED_PRICE:
            listing.fixed_price = data.get('fixed_price')
            listing.is_negotiable = data.get('is_negotiable', False)
            listing.current_price = listing.fixed_price
        elif listing.sale_mode == SaleMode.NAME_YOUR_PRICE:
            listing.min_price = data.get('min_price')
            listing.private_offers = data.get('private_offers', False)
        elif listing.sale_mode == SaleMode.AUCTION:
            listing.start_price = data.get('start_price')
            listing.current_price = listing.start_price
            listing.bid_step = data.get('bid_step', 1.00)
            if data.get('end_time'):
                listing.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        listing.allow_queue = data.get('allow_queue', False)
        
        db.session.add(listing)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'listing_id': listing.id
        })
        
    except Exception as e:
        app.logger.error(f"Error creating listing: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create listing'}), 500

@app.route('/api/listings/<int:listing_id>/photos', methods=['POST'])
def upload_photos(listing_id):
    """Upload photos for a listing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Verify listing ownership
    user_id = session['user_id']
    listing = Listing.query.filter_by(id=listing_id, seller_id=user_id).first()
    if not listing:
        return jsonify({'error': 'Listing not found or access denied'}), 404
    
    try:
        uploaded_files = []
        
        for file_key in request.files:
            file = request.files[file_key]
            if file and file.filename:
                filename = process_uploaded_image(file)
                if filename:
                    # Get current max order
                    max_order = db.session.query(db.func.max(ListingPhoto.order)).filter_by(listing_id=listing_id).scalar() or 0
                    
                    photo = ListingPhoto(
                        filename=filename,
                        order=max_order + 1,
                        listing_id=listing_id
                    )
                    db.session.add(photo)
                    uploaded_files.append({
                        'id': photo.id,
                        'filename': filename,
                        'url': f"/static/uploads/{filename}",
                        'order': photo.order
                    })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'photos': uploaded_files
        })
        
    except Exception as e:
        app.logger.error(f"Error uploading photos: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to upload photos'}), 500

@app.route('/api/listings/<int:listing_id>/publish', methods=['POST'])
def publish_listing(listing_id):
    """Publish a listing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    listing = Listing.query.filter_by(id=listing_id, seller_id=user_id).first()
    if not listing:
        return jsonify({'error': 'Listing not found or access denied'}), 404
    
    try:
        listing.status = ListingStatus.ACTIVE
        listing.published_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        app.logger.error(f"Error publishing listing: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to publish listing'}), 500

@app.route('/api/listings/<int:listing_id>/close', methods=['POST'])
def close_listing(listing_id):
    """Close a listing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    listing = Listing.query.filter_by(id=listing_id, seller_id=session['user_id']).first()
    if not listing:
        return jsonify({'error': 'Listing not found or access denied'}), 404
    
    try:
        listing.status = ListingStatus.CLOSED
        listing.closed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        app.logger.error(f"Error closing listing: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to close listing'}), 500

@app.route('/api/listings/<int:listing_id>/bid', methods=['POST'])
def place_bid(listing_id):
    """Place a bid on a listing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    listing = Listing.query.get_or_404(listing_id)
    
    if listing.seller_id == session['user_id']:
        return jsonify({'error': 'Cannot bid on your own listing'}), 400
    
    if listing.status != ListingStatus.ACTIVE:
        return jsonify({'error': 'Listing is not active'}), 400
    
    try:
        data = request.get_json()
        amount = float(data['amount'])
        message = data.get('message', '')
        
        # Validate bid amount
        if listing.sale_mode == SaleMode.AUCTION:
            min_bid = float(listing.current_price) + float(listing.bid_step)
            if amount < min_bid:
                return jsonify({'error': f'Bid must be at least ${min_bid:.2f}'}), 400
        
        # Create bid
        bid = Bid(
            amount=amount,
            message=message,
            listing_id=listing_id,
            bidder_id=session['user_id'],
            is_private=listing.sale_mode == SaleMode.NAME_YOUR_PRICE and listing.private_offers
        )
        
        db.session.add(bid)
        
        # Update listing current price for auctions
        if listing.sale_mode == SaleMode.AUCTION:
            listing.current_price = amount
        
        db.session.commit()
        
        return jsonify({'success': True, 'bid_id': bid.id})
        
    except Exception as e:
        app.logger.error(f"Error placing bid: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to place bid'}), 500

@app.route('/api/listings/<int:listing_id>')
def get_listing(listing_id):
    """Get listing details"""
    listing = Listing.query.get_or_404(listing_id)
    
    # Get photos
    photos = [{'url': f"/static/uploads/{photo.filename}", 'order': photo.order} 
              for photo in listing.photos]
    
    # Get bids (only public ones unless owner)
    bids_query = Bid.query.filter_by(listing_id=listing_id)
    if session.get('user_id') != listing.seller_id:
        bids_query = bids_query.filter_by(is_private=False)
    
    bids = bids_query.order_by(desc(Bid.created_at)).all()
    
    bid_list = [{
        'amount': float(bid.amount),
        'message': bid.message,
        'created_at': bid.created_at.isoformat(),
        'bidder_name': bid.bidder.first_name or bid.bidder.username or 'Anonymous'
    } for bid in bids]
    
    # Calculate time remaining for auctions
    time_remaining = None
    if listing.sale_mode == SaleMode.AUCTION and listing.end_time:
        time_remaining = calculate_time_remaining(listing.end_time)
    
    return jsonify({
        'id': listing.id,
        'title': listing.title,
        'description': listing.description,
        'sale_mode': listing.sale_mode.value,
        'current_price': float(listing.current_price) if listing.current_price else None,
        'status': listing.status.value,
        'photos': photos,
        'bids': bid_list,
        'time_remaining': time_remaining,
        'seller_name': listing.seller.first_name or listing.seller.username,
        'is_owner': session.get('user_id') == listing.seller_id
    })

@app.template_filter('format_price')
def format_price_filter(amount):
    return format_price(amount)

@app.template_filter('time_ago')
def time_ago_filter(dt):
    """Format datetime as time ago"""
    if not dt:
        return ""
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"
