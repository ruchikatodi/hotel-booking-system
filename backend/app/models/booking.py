"""
Booking Model
Represents a room booking by a customer
"""

from app import db
from datetime import datetime, date


class Booking(db.Model):
    """
    Booking Model - When a user books a room
    
    Attributes:
    - booking_id: Unique identifier
    - user_id: Which user made the booking
    - room_id: Which room was booked
    - check_in_date: When they arrive
    - check_out_date: When they leave
    - guests: How many people
    - total_amount: Total price
    - status: Current booking status
    - special_requests: Any special needs (extra bed, late checkout, etc.)
    """
    __tablename__ = 'bookings'
    
    booking_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.room_id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    special_requests = db.Column(db.Text)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancellation_reason = db.Column(db.Text)
    cancelled_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='bookings')
    room = db.relationship('Room', back_populates='bookings')
    payment = db.relationship('Payment', back_populates='booking', uselist=False, cascade='all, delete-orphan')
    
    # Status constants
    STATUS_PENDING = 'pending'  # Just created, waiting for payment
    STATUS_CONFIRMED = 'confirmed'  # Payment received
    STATUS_CHECKED_IN = 'checked_in'  # Guest arrived
    STATUS_CHECKED_OUT = 'checked_out'  # Guest left
    STATUS_CANCELLED = 'cancelled'  # Booking cancelled
    
    def __init__(self, user_id, room_id, check_in_date, check_out_date, guests, total_amount, special_requests="", status="pending",
             ):
        """Constructor"""
        # Validate dates
        if check_out_date <= check_in_date:
            raise ValueError("Check-out must be after check-in")
        
        self.user_id = user_id
        self.room_id = room_id
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.guests = guests
        self.total_amount = total_amount
        self.special_requests = special_requests
        self.status = status              # ✅ now allowed

    
    @property
    def nights(self):
        """Calculate number of nights"""
        return (self.check_out_date - self.check_in_date).days
    
    @property
    def is_active(self):
        """Check if booking is still active"""
        return self.status not in ['cancelled', 'checked_out']
    
    @property
    def is_upcoming(self):
        """Check if booking is in the future"""
        return self.check_in_date > date.today() and self.is_active
    
    @property
    def is_current(self):
        """Check if guest is currently checked in"""
        today = date.today()
        return (self.status == 'checked_in' and 
                self.check_in_date <= today <= self.check_out_date)
    
    @property
    def can_cancel(self):
        """Check if booking can still be cancelled"""
        return self.status in ['pending', 'confirmed'] and self.check_in_date > date.today()
    
    def confirm(self):
        """Mark booking as confirmed (payment received)"""
        if self.status != self.STATUS_PENDING:
            raise ValueError(f"Cannot confirm booking in {self.status} status")
        self.status = self.STATUS_CONFIRMED
    
    def check_in(self):
        """Check in the guest"""
        if self.status != self.STATUS_CONFIRMED:
            raise ValueError(f"Cannot check in from {self.status} status")
        self.status = self.STATUS_CHECKED_IN
    
    def check_out(self):
        """Check out the guest"""
        if self.status != self.STATUS_CHECKED_IN:
            raise ValueError(f"Cannot check out from {self.status} status")
        self.status = self.STATUS_CHECKED_OUT
    
    def cancel(self, reason=""):
        """Cancel the booking"""
        if not self.can_cancel:
            raise ValueError(f"Cannot cancel booking in {self.status} status")
        self.status = self.STATUS_CANCELLED
        self.cancellation_reason = reason
        self.cancelled_at = datetime.utcnow()
    
    def calculate_refund(self):
        """
        Calculate refund amount based on cancellation policy
        - 7+ days before: 100% refund
        - 3-7 days before: 50% refund
        - Less than 3 days: no refund
        """
        if self.status != self.STATUS_CANCELLED:
            return 0.0
        
        days_before = (self.check_in_date - date.today()).days
        
        if days_before >= 7:
            return self.total_amount  # Full refund
        elif days_before >= 3:
            return self.total_amount * 0.5  # 50% refund
        else:
            return 0.0  # No refund
    
    def to_dict(self, include_payment=False):
        """Convert to dictionary"""
        data = {
            'booking_id': self.booking_id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'guests': self.guests,
            'nights': self.nights,
            'total_amount': self.total_amount,
            'status': self.status,
            'special_requests': self.special_requests,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'is_upcoming': self.is_upcoming,
            'is_current': self.is_current,
            'can_cancel': self.can_cancel
        }
        
        if include_payment and self.payment:
            data['payment'] = self.payment.to_dict()
        
        return data
    
    def __repr__(self):
        return f"<Booking {self.booking_id} - Room {self.room_id} ({self.status})>"