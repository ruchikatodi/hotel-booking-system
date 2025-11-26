"""
User Model and Room Category Model
These are SQLAlchemy models that represent database tables
"""

from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """
    User Model - Represents a customer or admin
    
    Attributes:
    - user_id: Unique identifier
    - email: Email address (unique)
    - password_hash: Hashed password (NOT stored as plain text for security!)
    - first_name, last_name: User's name
    - phone: Phone number
    - role: 'customer' or 'admin'
    - is_active: Whether account is active
    - created_at, updated_at: Timestamps
    """
    __tablename__ = 'users'
    
    # Column definitions
    user_id = db.Column(db.Integer, primary_key=True)  # Primary key - unique identifier
    email = db.Column(db.String(255), unique=True, nullable=False)  # unique=True means no duplicates
    password_hash = db.Column(db.String(255), nullable=False)  # nullable=False means required
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='customer')  # default value is 'customer'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Auto-set current time
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (links to other tables)
    bookings = db.relationship('Booking', back_populates='user', cascade='all, delete-orphan')
    loyalty = db.relationship('LoyaltyPoints', back_populates='user', uselist=False)
    
    def __init__(self, email, password, first_name, last_name, phone=None, role='customer'):
        """Constructor - called when creating a new User"""
        self.email = email.lower().strip()  # Normalize email
        self.password_hash = generate_password_hash(password)  # Hash password for security
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.phone = phone
        self.role = role
    
    def verify_password(self, password):
        """
        Check if given password matches stored hash
        Returns: True if password is correct, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Update password"""
        self.password_hash = generate_password_hash(password)
    
    @property  # This allows us to use full_name like an attribute
    def full_name(self):
        """Derived property - combines first and last name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def to_dict(self, include_sensitive=False):
        """
        Convert User object to dictionary (for sending to frontend)
        include_sensitive: whether to include password hash
        """
        data = {
            'user_id': self.user_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return data
    
    def __repr__(self):
        """String representation - used for debugging"""
        return f"<User {self.email} ({self.role})>"


class RoomCategory(db.Model):
    """
    Room Category Model - Different types of rooms (Standard, Deluxe, Suite)
    
    Attributes:
    - category_id: Unique identifier
    - name: Category name (e.g., "Deluxe Room")
    - base_price: Base price per night
    - capacity: Maximum guests
    - amenities: List of features
    """
    __tablename__ = 'room_categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.String(500))  # Stored as comma-separated string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rooms = db.relationship('Room', back_populates='category')
    
    def __init__(self, name, description, base_price, capacity, amenities=None):
        """Constructor"""
        self.name = name
        self.description = description
        self.base_price = base_price
        self.capacity = capacity
        # Convert list to string if needed
        if amenities:
            self.amenities = ', '.join(amenities) if isinstance(amenities, list) else amenities
        else:
            self.amenities = ""
    
    def get_amenities_list(self):
        """Convert amenities string back to list"""
        if self.amenities:
            return [a.strip() for a in self.amenities.split(',')]
        return []
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'base_price': self.base_price,
            'capacity': self.capacity,
            'amenities': self.get_amenities_list(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<RoomCategory {self.name} (₹{self.base_price})>"


class LoyaltyPoints(db.Model):
    """
    Loyalty Points Model - Track customer rewards
    
    Tiers: bronze → silver → gold → platinum
    """
    __tablename__ = 'loyalty_points'
    
    loyalty_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, unique=True)
    points = db.Column(db.Integer, default=0)  # Reward points
    tier = db.Column(db.String(20), default='bronze')
    total_bookings = db.Column(db.Integer, default=0)  # How many times they've booked
    total_spent = db.Column(db.Float, default=0.0)  # Total money spent
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='loyalty')
    
    def update_tier(self):
        """Update tier based on number of bookings"""
        if self.total_bookings >= 20:
            self.tier = 'platinum'
        elif self.total_bookings >= 10:
            self.tier = 'gold'
        elif self.total_bookings >= 5:
            self.tier = 'silver'
        else:
            self.tier = 'bronze'
    
    def add_points(self, amount):
        """Add loyalty points"""
        self.points += amount
    
    def to_dict(self):
        return {
            'loyalty_id': self.loyalty_id,
            'user_id': self.user_id,
            'points': self.points,
            'tier': self.tier,
            'total_bookings': self.total_bookings,
            'total_spent': self.total_spent
        }
    
    def __repr__(self):
        return f"<LoyaltyPoints user_id={self.user_id} tier={self.tier}>"