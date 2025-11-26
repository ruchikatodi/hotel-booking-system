"""
Payment Model
Tracks all payments for bookings
"""

from app import db
from datetime import datetime


class Payment(db.Model):
    """
    Payment Model - Financial transaction for a booking
    
    Attributes:
    - payment_id: Unique identifier
    - booking_id: Which booking this payment is for
    - amount: Payment amount
    - payment_method: How they paid (credit card, UPI, etc.)
    - payment_status: Whether payment went through
    - transaction_id: Reference ID from payment processor
    """
    __tablename__ = 'payments'
    
    payment_id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.booking_id'), nullable=False, unique=True)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100), unique=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    refund_amount = db.Column(db.Float, default=0.0)
    refund_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    booking = db.relationship('Booking', back_populates='payment')
    
    # Payment method constants
    METHOD_CREDIT_CARD = 'credit_card'
    METHOD_DEBIT_CARD = 'debit_card'
    METHOD_UPI = 'upi'
    METHOD_NET_BANKING = 'net_banking'
    METHOD_CASH = 'cash'
    
    # Status constants
    STATUS_PENDING = 'pending'  # Waiting for payment
    STATUS_COMPLETED = 'completed'  # Payment received
    STATUS_FAILED = 'failed'  # Payment failed
    STATUS_REFUNDED = 'refunded'  # Money returned to customer
    
    def __init__(self, booking_id, amount, payment_method, transaction_id="", notes=""):
        """Constructor"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        self.booking_id = booking_id
        self.amount = amount
        self.payment_method = payment_method
        self.transaction_id = transaction_id
        self.notes = notes
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.payment_status == self.STATUS_COMPLETED
    
    @property
    def net_amount(self):
        """Amount after refunds"""
        return self.amount - self.refund_amount
    
    def mark_as_completed(self, transaction_id):
        """Mark payment as successfully completed"""
        if self.payment_status and self.payment_status!= self.STATUS_PENDING:
            raise ValueError(f"Cannot mark {self.payment_status} payment as completed")
        
        self.payment_status = self.STATUS_COMPLETED
        self.transaction_id = transaction_id
        self.payment_date = datetime.utcnow()
    
    def mark_as_failed(self, reason=""):
        """Mark payment as failed"""
        if self.payment_status != self.STATUS_PENDING:
            raise ValueError(f"Cannot mark {self.payment_status} payment as failed")
        
        self.payment_status = self.STATUS_FAILED
        if reason:
            self.notes = f"Failed: {reason}"
    
    def process_refund(self, refund_amount, reason=""):
        """
        Process a refund
        refund_amount: How much to refund
        """
        if self.payment_status != self.STATUS_COMPLETED:
            raise ValueError("Can only refund completed payments")
        
        if refund_amount <= 0 or refund_amount > self.amount:
            raise ValueError(f"Invalid refund amount: {refund_amount}")
        
        if self.refund_amount + refund_amount > self.amount:
            raise ValueError("Total refund cannot exceed payment amount")
        
        self.refund_amount += refund_amount
        self.refund_date = datetime.utcnow()
        
        # If fully refunded, mark status as refunded
        if self.refund_amount >= self.amount:
            self.payment_status = self.STATUS_REFUNDED
        
        if reason:
            self.notes = f"Refunded: {reason}"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'payment_id': self.payment_id,
            'booking_id': self.booking_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'transaction_id': self.transaction_id,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'refund_amount': self.refund_amount,
            'refund_date': self.refund_date.isoformat() if self.refund_date else None,
            'net_amount': self.net_amount,
            'is_successful': self.is_successful,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f"<Payment {self.payment_id} - ₹{self.amount} ({self.payment_status})>"