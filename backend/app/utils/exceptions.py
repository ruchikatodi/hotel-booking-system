"""
Custom Exception Classes
These are custom error types for our application
When something goes wrong, we raise these exceptions with a clear error message
"""

class HotelBookingException(Exception):
    """
    Base exception class - all our custom exceptions inherit from this
    This allows us to catch all booking system errors with one catch block
    """
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary to send to frontend"""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code
        }


# Authentication Errors
class AuthenticationException(HotelBookingException):
    """Raised when login/auth fails"""
    def __init__(self, message="Authentication failed"):
        super().__init__(message, error_code='AUTH_ERROR')


class AuthorizationException(HotelBookingException):
    """Raised when user lacks permission"""
    def __init__(self, message="Insufficient permissions"):
        super().__init__(message, error_code='PERMISSION_DENIED')


# Validation Errors
class ValidationException(HotelBookingException):
    """Raised when input data is invalid"""
    def __init__(self, message, field=None):
        super().__init__(message, error_code='VALIDATION_ERROR')
        self.field = field
    
    def to_dict(self):
        result = super().to_dict()
        if self.field:
            result['field'] = self.field
        return result


# User Errors
class UserNotFoundException(HotelBookingException):
    """Raised when user doesn't exist"""
    def __init__(self, user_id):
        message = f"User with ID {user_id} not found"
        super().__init__(message, error_code='USER_NOT_FOUND')


class DuplicateUserException(HotelBookingException):
    """Raised when trying to create user that already exists"""
    def __init__(self, email):
        message = f"User with email '{email}' already exists"
        super().__init__(message, error_code='DUPLICATE_USER')


# Room Errors
class RoomNotFoundException(HotelBookingException):
    """Raised when room doesn't exist"""
    def __init__(self, room_id):
        message = f"Room with ID {room_id} not found"
        super().__init__(message, error_code='ROOM_NOT_FOUND')


class RoomUnavailableException(HotelBookingException):
    """Raised when room is not available for booking"""
    def __init__(self, room_id, check_in, check_out):
        message = f"Room {room_id} is not available from {check_in} to {check_out}"
        super().__init__(message, error_code='ROOM_UNAVAILABLE')


class CapacityExceededException(ValidationException):
    """Raised when guest count exceeds room capacity"""
    def __init__(self, guests, capacity):
        message = f"Guest count ({guests}) exceeds room capacity ({capacity})"
        super().__init__(message, field='guests')


# Booking Errors
class BookingNotFoundException(HotelBookingException):
    """Raised when booking doesn't exist"""
    def __init__(self, booking_id):
        message = f"Booking with ID {booking_id} not found"
        super().__init__(message, error_code='BOOKING_NOT_FOUND')


class InvalidDateRangeException(ValidationException):
    """Raised when check-out is before check-in"""
    def __init__(self, check_in, check_out):
        message = f"Check-out date must be after check-in date"
        super().__init__(message, field='date_range')


class CancellationException(HotelBookingException):
    """Raised when booking cannot be cancelled"""
    def __init__(self, message, booking_id=None):
        super().__init__(message, error_code='CANCELLATION_ERROR')


# Payment Errors
class PaymentException(HotelBookingException):
    """Raised when payment processing fails"""
    def __init__(self, message, transaction_id=None):
        super().__init__(message, error_code='PAYMENT_ERROR')


class PaymentNotFoundException(HotelBookingException):
    """Raised when payment record doesn't exist"""
    def __init__(self, payment_id):
        message = f"Payment with ID {payment_id} not found"
        super().__init__(message, error_code='PAYMENT_NOT_FOUND')


class RefundException(HotelBookingException):
    """Raised when refund processing fails"""
    def __init__(self, message):
        super().__init__(message, error_code='REFUND_ERROR')


# Database Errors
class DatabaseException(HotelBookingException):
    """Raised when database operations fail"""
    def __init__(self, message):
        super().__init__(message, error_code='DATABASE_ERROR')