"""
Booking Routes
Handles room search, booking creation, booking management, and cancellations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Room, Booking, RoomCategory, LoyaltyPoints, Payment
from app.utils.exceptions import (
    ValidationException, RoomNotFoundException, BookingNotFoundException,
    UserNotFoundException, RoomUnavailableException, CapacityExceededException,
    InvalidDateRangeException, CancellationException
)
from datetime import datetime, date, timedelta
import traceback

bp = Blueprint('booking', __name__)


# ============== SEARCH AVAILABLE ROOMS ==============
@bp.route('/search', methods=['GET'])
def search_rooms():
    """
    Search for available room CATEGORIES (not individual rooms)
    Returns categories with availability count
    
    Query Parameters:
    - check_in: Date in format YYYY-MM-DD (required)
    - check_out: Date in format YYYY-MM-DD (required)
    - guests: Number of guests (required)
    
    Example:
    GET /api/bookings/search?check_in=2024-12-20&check_out=2024-12-25&guests=2
    
    Response:
    {
        "check_in": "2024-12-20",
        "check_out": "2024-12-25",
        "guests": 2,
        "nights": 5,
        "available_categories": [
            {
                "category_id": 2,
                "name": "Standard Room",
                "description": "...",
                "base_price": 100.00,
                "capacity": 2,
                "amenities": [...],
                "available_count": 5,
                "total_price": 500.00
            }
        ]
    }
    """
    try:
        # Get query parameters
        check_in_str = request.args.get('check_in')
        check_out_str = request.args.get('check_out')
        guests = request.args.get('guests', type=int)
        
        # Validate required parameters
        if not check_in_str or not check_out_str or not guests:
            raise ValidationException(
                "check_in, check_out, and guests are required"
            )
        
        # Parse dates
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationException(
                "Dates must be in YYYY-MM-DD format",
                field="dates"
            )
        
        # Validate date range
        if check_out <= check_in:
            raise InvalidDateRangeException(check_in, check_out)
        
        # Validate guests
        if guests <= 0:
            raise ValidationException("Guests must be at least 1", field="guests")
        
        # Calculate nights
        nights = (check_out - check_in).days
        
        # Get all room categories that can accommodate the guests
        categories = RoomCategory.query.filter(
            RoomCategory.capacity >= guests
        ).all()
        
        available_categories = []
        
        for category in categories:
            # Get ALL active/clean rooms in this category (or just all rooms)
            rooms_in_category = Room.query.filter_by(
                category_id=category.category_id
                # Remove: status='available'  ← REMOVE THIS LINE
            ).all()

            available_count = 0

            for room in rooms_in_category:
                available_count = db.session.query(Room).filter(
                    Room.category_id == category.category_id,
                    ~db.session.query(Booking).filter(
                        Booking.room_id == Room.room_id,
                        Booking.status.in_(['confirmed', 'checked_in', 'pending']),
                        Booking.check_in_date < check_out,
                        Booking.check_out_date > check_in
                    ).exists()
                ).count()

            if available_count > 0:
                total_price = category.base_price * nights
                available_categories.append({
                    'category_id': category.category_id,
                    'name': category.name,
                    'description': category.description or "",
                    'base_price': float(category.base_price),
                    'price_per_night': float(category.base_price),
                    'capacity': category.capacity,
                    'amenities': category.get_amenities_list(),
                    'available_count': available_count,
                    'total_price': float(total_price),
                    'nights': nights
                })
                
        return jsonify({
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'guests': guests,
            'nights': nights,
            'available_categories': available_categories,
            'total_found': len(available_categories)
        }), 200
        
    except (ValidationException, InvalidDateRangeException) as e:
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'SearchError',
            'message': str(e)
        }), 500


# ============== CREATE BOOKING ==============
@bp.route('', methods=['POST'])
@jwt_required()
def create_booking():
    """
    Create a new booking
    
    Requires: Authorization header with Bearer token
    
    Request (POST):
    {
        "room_id": 3,
        "check_in_date": "2024-12-20",
        "check_out_date": "2024-12-25",
        "guests": 2,
        "special_requests": "Late check-in, extra bed"
    }
    
    Response:
    {
        "message": "Booking created successfully",
        "booking": { ... booking details ... }
    }
    """
    try:
        print("🔍 Starting booking creation...")

        user_id = int(get_jwt_identity())
        print(f"✅ User ID: {user_id}")

        data = request.get_json()
        print(f"📝 Request data: {data}")

        # ---- VALIDATION ----
        required_fields = ['category_id', 'check_in_date', 'check_out_date', 'guests']
        for field in required_fields:
            if field not in data:
                raise ValidationException(f"{field} is required", field=field)

        category_id = data['category_id']
        guests = data['guests']

        # ---- PARSE DATES ----
        try:
            check_in = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
            check_out = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValidationException("Dates must be in YYYY-MM-DD format", field="dates")

        if check_out <= check_in:
            raise InvalidDateRangeException(check_in, check_out)

        print(f"📅 Dates: {check_in} → {check_out}")

        # ---- USER CHECK ----
        user = User.query.get(user_id)
        if not user:
            raise UserNotFoundException(user_id)

        # ---- CATEGORY CHECK ----
        category = RoomCategory.query.get(category_id)
        if not category:
            raise ValidationException("Invalid category_id", field="category_id")

        if guests > category.capacity:
            raise CapacityExceededException(guests, category.capacity)

        print(f"👤 Guest capacity OK (max {category.capacity})")

        # ---- AUTO-ASSIGN AVAILABLE ROOM ----
        print("🔍 Searching for available rooms...")

        rooms_in_category = Room.query.filter_by(category_id=category_id).all()
        if not rooms_in_category:
            raise RoomNotFoundException(f"No rooms exist for category {category_id}")

        available_room = None
        for room in rooms_in_category:
            conflicting = Booking.query.filter(
                Booking.room_id == room.room_id,
                Booking.status.in_(['confirmed', 'checked_in','pending']),
                Booking.check_in_date < check_out,
                Booking.check_out_date > check_in
            ).first()

            if not conflicting:
                available_room = room
                break

        if not available_room:
            raise RoomUnavailableException(
                f"No rooms available for category {category_id}",
                check_in,
                check_out
            )

        print(f"🏨 Assigned Room → {available_room.room_number}")

        # ---- PRICE CALC ----
        nights = (check_out - check_in).days
        total_amount = category.base_price * nights
        print(f"💰 Total Price: {total_amount} ({nights} nights)")

        # ---- CREATE BOOKING ----
        booking = Booking(
            user_id=user_id,
            room_id=available_room.room_id,
            check_in_date=check_in,
            check_out_date=check_out,
            guests=guests,
            total_amount=total_amount,
            special_requests=data.get('special_requests', ''),
            status="pending"
        )

        db.session.add(booking)
        db.session.commit()

        print("✅ Booking saved successfully")
        print(f"📝 Booking ID: {booking.booking_id}") 

        return jsonify({
            "message": "Booking created successfully",
            "assigned_room": available_room.room_number,
            "booking_id": booking.booking_id,
            "booking": booking.to_dict()
        }), 201

    # ---- HANDLE EXPECTED ERRORS ----
    except (ValidationException, RoomNotFoundException, UserNotFoundException,
            RoomUnavailableException, CapacityExceededException,
            InvalidDateRangeException) as e:

        db.session.rollback()
        print(f"❌ Expected error: {e.message}")
        return jsonify(e.to_dict()), 400

    # ---- UNEXPECTED ERRORS ----
    except Exception as e:
        db.session.rollback()
        print(f"❌ Unexpected error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'BookingError',
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500


# ============== GET USER'S BOOKINGS ==============
@bp.route('/my-bookings', methods=['GET'])
@jwt_required()
def get_my_bookings():
    """
    Get all bookings for current user
    
    Requires: Authorization header with Bearer token
    
    Query Parameters (optional):
    - status: Filter by status (pending, confirmed, checked_in, etc.)
    - filter: 'upcoming', 'past', 'active', or 'all' (default: 'upcoming')
    
    Response:
    {
        "total_bookings": 3,
        "bookings": [ ... ]
    }
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Get filter type
        filter_type = request.args.get('filter')
        status_filter = request.args.get('status')
        
        # Base query
        query = Booking.query.filter_by(user_id=user_id)
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Apply time filter
        today = date.today()
        
        if filter_type == 'upcoming':
            query = query.filter(Booking.check_in_date > today)
        elif filter_type == 'past':
            query = query.filter(Booking.check_out_date <= today)
        elif filter_type == 'active':
            query = query.filter(
                (Booking.check_in_date <= today) &
                (Booking.check_out_date >= today)
            )
        # 'all' has no additional filter
        
        # Get bookings ordered by check-in date (newest first)
        bookings = query.order_by(Booking.check_in_date.desc()).all()
        
        bookings_data = [b.to_dict(include_payment=True) for b in bookings]
        
        return jsonify({
            'total_bookings': len(bookings_data),
            'filter': filter_type,
            'bookings': bookings_data
        }), 200
        
    except Exception as e:
        print(f"❌ Get bookings error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'BookingsError',
            'message': 'An error occurred fetching bookings'
        }), 500


# ============== GET SINGLE BOOKING ==============
@bp.route('/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """
    Get details of a specific booking
    
    Requires: Authorization header with Bearer token
    
    Response:
    {
        "booking": { ... all booking details ... }
    }
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Get booking
        booking = Booking.query.get(booking_id)
        
        if not booking:
            raise BookingNotFoundException(booking_id)
        
        # Check that user owns this booking
        if booking.user_id != user_id:
            from app.utils.exceptions import AuthorizationException
            raise AuthorizationException("You can only view your own bookings")
        
        return jsonify({
            'booking': booking.to_dict(include_payment=True)
        }), 200
        
    except Exception as e:
        if isinstance(e, BookingNotFoundException):
            return jsonify(e.to_dict()), 404
        print(f"❌ Get booking error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'BookingError',
            'message': 'An error occurred fetching booking'
        }), 500


# ============== CANCEL BOOKING ==============
@bp.route('/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    """
    Cancel a booking
    
    Requires: Authorization header with Bearer token
    
    Request (POST):
    {
        "reason": "Change of plans"
    }
    
    Response:
    {
        "message": "Booking cancelled successfully",
        "booking": { ... updated booking ... },
        "refund_amount": 500.0
    }
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        
        # Get booking
        booking = Booking.query.get(booking_id)
        
        if not booking:
            raise BookingNotFoundException(booking_id)
        
        # Check ownership
        if booking.user_id != user_id:
            from app.utils.exceptions import AuthorizationException
            raise AuthorizationException("You can only cancel your own bookings")
        
        # Check if can cancel
        if not booking.can_cancel:
            raise CancellationException(
                f"Cannot cancel booking in {booking.status} status",
                booking_id=booking_id
            )
        
        days_before = (booking.check_in_date - date.today()).days
        if days_before >= 7:
            refund_amount = booking.total_amount
        elif days_before >= 3:
            refund_amount = booking.total_amount * 0.5
        else:
            refund_amount = 0.0
        
        # Cancel booking
        reason = data.get('reason', '')
        booking.cancel(reason)
        
        # Update loyalty points (deduct points for cancellation)
        loyalty = LoyaltyPoints.query.filter_by(user_id=user_id).first()
        if loyalty and loyalty.points > 0:
            loyalty.points = max(0, loyalty.points - 50)  # Deduct 50 points
        
        db.session.commit()
        
        return jsonify({
            'message': 'Booking cancelled successfully',
            'booking': booking.to_dict(),
            'refund_amount': refund_amount
        }), 200
        
    except (BookingNotFoundException, CancellationException) as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Cancel booking error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'CancellationError',
            'message': 'An error occurred cancelling booking'
        }), 500
# ============== QR CODE SELF CHECK-IN ==============
@bp.route('/<int:booking_id>/qr-checkin', methods=['PATCH'])
@jwt_required()
def qr_checkin(booking_id):
    """
    Self check-in using QR code simulation
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Get booking
        booking = Booking.query.get(booking_id)
        
        if not booking:
            raise BookingNotFoundException(booking_id)
            
        # Check ownership
        if booking.user_id != user_id:
            from app.utils.exceptions import AuthorizationException
            raise AuthorizationException("You can only check in for your own bookings")
            
        # Perform check-in
        if booking.status != Booking.STATUS_CONFIRMED:
            raise ValidationException(
                f"Cannot check in. Current booking status is '{booking.status}'. Booking must be confirmed (paid) first.",
                field='status'
            )
            
        booking.status = Booking.STATUS_CHECKED_IN
        db.session.commit()
        
        return jsonify({
            'message': 'Check-in successful! Welcome to Novacrest Hotel.',
            'booking': booking.to_dict()
        }), 200
        
    except (BookingNotFoundException, ValidationException) as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 400
    except Exception as e:
        db.session.rollback()
        print(f"❌ QR check-in error: {str(e)}")
        return jsonify({
            'error': 'CheckInError',
            'message': 'An unexpected error occurred during check-in'
        }), 500


# ============== GET ROOM CATEGORIES ==============
@bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Get all room categories
    No authentication required - anyone can see room types
    
    Response:
    {
        "categories": [
            {
                "category_id": 1,
                "name": "Standard Room",
                "base_price": 100.0,
                "capacity": 2,
                "amenities": ["WiFi", "TV", "AC"]
            },
            ...
        ]
    }
    """
    try:
        categories = RoomCategory.query.all()
        categories_data = [c.to_dict() for c in categories]
        
        return jsonify({
            'total_categories': len(categories_data),
            'categories': categories_data
        }), 200
        
    except Exception as e:
        print(f"❌ Get categories error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'CategoriesError',
            'message': 'An error occurred fetching categories'
        }), 500
