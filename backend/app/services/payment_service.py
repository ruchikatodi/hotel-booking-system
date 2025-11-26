from app import db
from app.models import Payment, Booking, LoyaltyPoints
from app.utils.exceptions import PaymentException, BookingNotFoundException
import uuid


class PaymentService:
    """
    Business logic for payment operations
    Handles payment processing and refunds
    """
    
    @staticmethod
    def process_payment(booking_id, amount, payment_method):
        """
        Process payment for a booking
        
        Handles:
        1. Validate payment
        2. Create payment record
        3. Update booking status
        4. Add loyalty points
        
        Returns: Payment object
        """
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)
        
        # Check booking status
        if booking.status != 'pending':
            raise PaymentException(f"Cannot pay for {booking.status} booking")
        
        # Check amount
        if amount != booking.total_amount:
            raise PaymentException(f"Amount mismatch: {amount} != {booking.total_amount}")
        
        # Check existing payment
        existing = Payment.query.filter_by(booking_id=booking_id).first()
        if existing:
            raise PaymentException("Payment already exists for this booking")
        
        # Generate transaction ID (in real app, from payment gateway)
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # Create payment
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id
        )
        
        # Simulate payment processing (in real app, call Stripe/Razorpay API)
        payment.mark_as_completed(transaction_id)
        
        # Update booking
        booking.status = 'confirmed'
        
        # Add loyalty points
        loyalty = LoyaltyPoints.query.filter_by(user_id=booking.user_id).first()
        if loyalty:
            points = int(amount / 10)  # 1 point per 10 rupees
            loyalty.points += points
            loyalty.total_bookings += 1
            loyalty.total_spent += amount
            loyalty.update_tier()
        
        db.session.add(payment)
        db.session.commit()
        
        return payment
    
    @staticmethod
    def get_payment_history(user_id):
        """Get all payments for a user"""
        bookings = Booking.query.filter_by(user_id=user_id).all()
        booking_ids = [b.booking_id for b in bookings]
        
        payments = Payment.query.filter(
            Payment.booking_id.in_(booking_ids)
        ).order_by(Payment.payment_date.desc()).all()
        
        return payments
