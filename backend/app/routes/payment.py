"""
Payment Routes
Handles payment processing, refunds, and payment history
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Booking, Payment, User, LoyaltyPoints, Room
from app.utils.exceptions import (
    ValidationException, BookingNotFoundException, PaymentNotFoundException,
    PaymentException, RefundException, AuthorizationException
)
from datetime import datetime
import uuid
import traceback

bp = Blueprint('payment', __name__)


# ============== PROCESS PAYMENT ==============
@bp.route('/process', methods=['POST'])
@jwt_required()
def process_payment():
    """
    Process payment for a booking
    
    Requires: Authorization header with Bearer token
    
    Request (POST):
    {
        "booking_id": 1,
        "payment_method": "credit_card",
        "amount": 500.0,
        "notes": "Payment for booking"
    }
    
    Response:
    {
        "message": "Payment processed successfully",
        "payment": { ... },
        "points_earned": 50
    }
    """
    try:
        print("🔍 Starting payment processing...")
        print(f"🔍 Request headers: {dict(request.headers)}")
        
        user_id = int(get_jwt_identity())
        print(f"✅ User ID from JWT: {user_id}")
        print(f"✅ User ID type: {type(user_id)}")
        
        # Verify user exists in database
        user = User.query.get(user_id)
        print(f"✅ User from DB: {user}")
        if user:
            print(f"   User email: {user.email}")
            print(f"   User role: {user.role}")
        
        data = request.get_json()
        print(f"📝 Payment data: {data}")
        
        # Validate required fields
        required_fields = ['booking_id', 'payment_method', 'amount']
        for field in required_fields:
            if field not in data:
                raise ValidationException(f"{field} is required", field=field)
        
        booking_id = data['booking_id']
        payment_method = data['payment_method']
        amount = data['amount']
        
        print(f"✅ Required fields present")
        
        # Validate payment method
        valid_methods = ['credit_card', 'debit_card', 'upi', 'net_banking', 'cash']
        if payment_method not in valid_methods:
            raise ValidationException(
                f"Invalid payment method. Valid: {', '.join(valid_methods)}",
                field="payment_method"
            )
        
        print(f"✅ Payment method valid: {payment_method}")
        
        # Validate amount
        if amount <= 0:
            raise ValidationException("Amount must be positive", field="amount")
        
        print(f"✅ Amount valid: {amount}")
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            print(f"❌ Booking {booking_id} not found")
            raise BookingNotFoundException(booking_id)
        
        print(f"✅ Booking found: {booking_id}")
        print(f"   Booking user_id from DB: {booking.user_id}")
        print(f"   Booking user_id type: {type(booking.user_id)}")
        print(f"   Current user_id: {user_id}")
        print(f"   Current user_id type: {type(user_id)}")
        
        # Convert to same type for comparison
        booking_user_id = int(booking.user_id)
        current_user_id = int(user_id)
        
        print(f"🔍 Checking ownership...")
        print(f"   Booking belongs to user: {booking_user_id}")
        print(f"   Current user: {current_user_id}")
        print(f"   Are they equal? {booking_user_id == current_user_id}")
        
        if booking_user_id != current_user_id:
            print(f"❌ User {current_user_id} trying to pay for booking of user {booking_user_id}")
            raise AuthorizationException("You can only pay for your own bookings")
        
        print(f"✅ User owns this booking")
        
        # Check booking status
        if booking.status != 'pending':
            raise PaymentException(
                f"Cannot pay for booking in {booking.status} status"
            )
        
        print(f"✅ Booking status is pending")
        
        # Check if amount matches booking total
        if amount != booking.total_amount:
            raise PaymentException(
                f"Amount ({amount}) must match booking total ({booking.total_amount})"
            )
        
        print(f"✅ Amount matches booking total")
        
        # Check if payment already exists
        existing_payment = Payment.query.filter_by(booking_id=booking_id).first()
        if existing_payment:
            raise PaymentException("Payment already exists for this booking")
        
        print(f"✅ No existing payment")
        
        # Generate transaction ID
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        print(f"✅ Transaction ID: {transaction_id}")
        
        # Create payment
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            notes=data.get('notes', '')
        )
        
        print(f"✅ Payment object created")
        
        # Mark payment as completed
        payment.mark_as_completed(transaction_id)
        print(f"✅ Payment marked as completed")
        
        # Update booking status
        booking.status = 'confirmed'
        print(f"✅ Booking status updated to confirmed")
        
        # Add loyalty points
        loyalty = LoyaltyPoints.query.filter_by(user_id=user_id).first()
        points_earned = 0
        if loyalty:
            points_earned = int(amount / 10)  # 1 point per 10 rupees
            loyalty.points += points_earned
            loyalty.total_bookings += 1
            loyalty.total_spent += amount
            loyalty.update_tier()
            print(f"✅ Loyalty points added: {points_earned}")
        
        # Update room status
        room = booking.room
        room.status = 'reserved'
        print(f"✅ Room status updated to reserved")
        
        # Save to database
        db.session.add(payment)
        db.session.commit()
        
        print(f"✅ Payment committed to database")
        
        return jsonify({
            'message': 'Payment processed successfully',
            'payment': payment.to_dict(),
            'booking': booking.to_dict(),
            'points_earned': points_earned,
            'transaction_id': transaction_id
        }), 201
        
    except (ValidationException, BookingNotFoundException, PaymentException, AuthorizationException) as e:
        db.session.rollback()
        print(f"❌ Expected error: {e.message}")
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Payment error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        traceback.print_exc()
        return jsonify({
            'error': 'PaymentError',
            'message': f'An error occurred: {str(e)}'
        }), 500


# ============== GET PAYMENT STATUS ==============
@bp.route('/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """
    Get payment details
    
    Requires: Authorization header with Bearer token
    
    Response:
    {
        "payment": { ... payment details ... }
    }
    """
    try:
        user_id = get_jwt_identity()
        
        # Get payment
        payment = Payment.query.get(payment_id)
        if not payment:
            raise PaymentNotFoundException(payment_id)
        
        # Check that user owns this booking
        booking = payment.booking
        if booking.user_id != user_id:
            raise AuthorizationException("You can only view your own payments")
        
        return jsonify({
            'payment': payment.to_dict()
        }), 200
        
    except (PaymentNotFoundException, AuthorizationException) as e:
        return jsonify(e.to_dict()), 404 if isinstance(e, PaymentNotFoundException) else 403
    except Exception as e:
        print(f"❌ Get payment error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'PaymentError',
            'message': 'An error occurred fetching payment'
        }), 500


# ============== GET PAYMENT FOR BOOKING ==============
@bp.route('/booking/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_payment_for_booking(booking_id):
    """
    Get payment for a specific booking
    
    Requires: Authorization header with Bearer token
    
    Response:
    {
        "payment": { ... } or null if no payment yet
    }
    """
    try:
        user_id = get_jwt_identity()
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)
        
        # Check ownership
        if booking.user_id != user_id:
            raise AuthorizationException("You can only view your own bookings")
        
        payment = Payment.query.filter_by(booking_id=booking_id).first()
        
        return jsonify({
            'payment': payment.to_dict() if payment else None
        }), 200
        
    except (BookingNotFoundException, AuthorizationException) as e:
        return jsonify(e.to_dict()), 404 if isinstance(e, BookingNotFoundException) else 403
    except Exception as e:
        print(f"❌ Get payment error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'PaymentError',
            'message': 'An error occurred fetching payment'
        }), 500


# ============== REQUEST REFUND ==============
@bp.route('/<int:payment_id>/refund', methods=['POST'])
@jwt_required()
def request_refund(payment_id):
    """
    Request refund for a payment
    
    Requires: Authorization header with Bearer token
    
    Request (POST):
    {
        "reason": "I need to cancel my booking"
    }
    
    Response:
    {
        "message": "Refund processed",
        "refund_amount": 500.0
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get payment
        payment = Payment.query.get(payment_id)
        if not payment:
            raise PaymentNotFoundException(payment_id)
        
        # Check ownership
        booking = payment.booking
        if booking.user_id != user_id:
            raise AuthorizationException("You can only refund your own payments")
        
        # Check if payment is completed
        if payment.payment_status != 'completed':
            raise RefundException(
                f"Cannot refund payment in {payment.payment_status} status"
            )
        
        # Check if booking can be cancelled
        if not booking.can_cancel:
            raise RefundException(
                f"Cannot refund: booking in {booking.status} status cannot be cancelled"
            )
        
        # Calculate refund amount
        refund_amount = booking.calculate_refund()
        
        if refund_amount <= 0:
            raise RefundException(
                "No refund available: booking is too close to check-in date"
            )
        
        # Process refund
        reason = data.get('reason', 'Customer requested refund')
        payment.process_refund(refund_amount, reason)
        
        # Cancel booking
        booking.cancel(reason)
        
        # Update room status
        room = booking.room
        room.status = 'available'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Refund processed successfully',
            'refund_amount': refund_amount,
            'payment_status': payment.payment_status,
            'booking_status': booking.status
        }), 200
        
    except (PaymentNotFoundException, RefundException, AuthorizationException) as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 400 if isinstance(e, RefundException) else 403
    except Exception as e:
        db.session.rollback()
        print(f"❌ Refund error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'RefundError',
            'message': 'An error occurred processing refund'
        }), 500


# ============== PAYMENT HISTORY ==============
@bp.route('/history', methods=['GET'])
@jwt_required()
def payment_history():
    """
    Get all payments for current user
    
    Requires: Authorization header with Bearer token
    
    Query Parameters (optional):
    - status: Filter by status (pending, completed, failed, refunded)
    
    Response:
    {
        "total_payments": 3,
        "payments": [ ... ]
    }
    """
    try:
        user_id = get_jwt_identity()
        status_filter = request.args.get('status')
        
        # Get all bookings for this user
        bookings = Booking.query.filter_by(user_id=user_id).all()
        booking_ids = [b.booking_id for b in bookings]
        
        # Get payments for these bookings
        query = Payment.query.filter(Payment.booking_id.in_(booking_ids))
        
        if status_filter:
            query = query.filter_by(payment_status=status_filter)
        
        payments = query.order_by(Payment.payment_date.desc()).all()
        payments_data = [p.to_dict() for p in payments]
        
        return jsonify({
            'total_payments': len(payments_data),
            'payments': payments_data
        }), 200
        
    except Exception as e:
        print(f"❌ Payment history error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'HistoryError',
            'message': 'An error occurred fetching payment history'
        }), 500