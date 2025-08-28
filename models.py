from app import db
from datetime import datetime
from enum import Enum

class SaleMode(Enum):
    FIXED_PRICE = "fixed_price"
    FREE = "free"
    NAME_YOUR_PRICE = "name_your_price"
    AUCTION = "auction"

class ListingStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SOLD = "sold"
    CLOSED = "closed"
    ENDED = "ended"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(64), nullable=True)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    listings = db.relationship('Listing', backref='seller', lazy=True)
    bids = db.relationship('Bid', backref='bidder', lazy=True)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    condition = db.Column(db.String(50), nullable=True)
    
    # Sale mode and pricing
    sale_mode = db.Column(db.Enum(SaleMode), nullable=False)
    fixed_price = db.Column(db.Numeric(10, 2), nullable=True)
    start_price = db.Column(db.Numeric(10, 2), nullable=True)
    min_price = db.Column(db.Numeric(10, 2), nullable=True)
    current_price = db.Column(db.Numeric(10, 2), nullable=True)
    bid_step = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Flags
    is_negotiable = db.Column(db.Boolean, default=False)
    allow_queue = db.Column(db.Boolean, default=False)
    private_offers = db.Column(db.Boolean, default=False)
    
    # Status and timing
    status = db.Column(db.Enum(ListingStatus), default=ListingStatus.DRAFT)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # Foreign keys
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    photos = db.relationship('ListingPhoto', backref='listing', lazy=True, cascade='all, delete-orphan')
    bids = db.relationship('Bid', backref='listing', lazy=True, cascade='all, delete-orphan')

class ListingPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, default=0)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)

class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_private = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
