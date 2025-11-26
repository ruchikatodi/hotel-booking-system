"""
Authentication Routes
Handles user registration, login, password changes, and profile management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, LoyaltyPoints
from app.utils.exceptions import (
    AuthenticationException, UserNotFoundException, 
    DuplicateUserException, ValidationException
)
from datetime import timedelta

# Create a blueprint (like a module of routes)
bp = Blueprint('auth', __name__)


# ============== REGISTRATION ==============
@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request (POST):
    {
        "email": "user@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890"
    }
    
    Response:
    {
        "message": "User registered successfully",
        "user_id": 1,
        "email": "user@example.com",
        "access_token": "eyJ..."
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate that we have all required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationException(f"{field} is required", field=field)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email'].lower()).first()
        if existing_user:
            raise DuplicateUserException(data['email'])
        
        # Validate password length (security)
        if len(data['password']) < 8:
            raise ValidationException(
                "Password must be at least 8 characters", 
                field="password"
            )
        
        # Create new user
        user = User(
            email=data['email'].lower(),
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone')
        )
        
        # Save user to database
        db.session.add(user)
        db.session.commit()
        
        # Create loyalty points record for new user
        loyalty = LoyaltyPoints(user_id=user.user_id)
        db.session.add(loyalty)
        db.session.commit()
        
        # Create authentication token (JWT)
        # Token expires in 7 days
        access_token = create_access_token(
            identity=str(user.user_id),
            expires_delta=timedelta(days=7)
        )
        
        # Return success response
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.user_id,
            'email': user.email,
            'full_name': user.full_name,
            'access_token': access_token
        }), 201  # 201 = Created
        
    except (ValidationException, DuplicateUserException, AuthenticationException) as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 400  # 400 = Bad Request
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Registration error: {str(e)}")
        return jsonify({
            'error': 'RegistrationError',
            'message': 'An error occurred during registration'
        }), 500  # 500 = Server Error


# ============== LOGIN ==============
@bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    
    Request (POST):
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "message": "Login successful",
        "user": { ... user data ... },
        "access_token": "eyJ..."
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            raise ValidationException("Email and password are required")
        
        # Find user by email
        user = User.query.filter_by(email=data['email'].lower()).first()
        
        if not user:
            raise AuthenticationException("Invalid email or password")
        
        # Check if account is active
        if not user.is_active:
            raise AuthenticationException("Account is deactivated. Please contact support.")
        
        # Verify password
        if not user.verify_password(data['password']):
            raise AuthenticationException("Invalid email or password")
        
        # Create authentication token
        access_token = create_access_token(
            identity=str(user.user_id),
            expires_delta=timedelta(days=7)
        )
        
        # Return user data and token
        return jsonify({
            'message': 'Login successful',
            'user_id': user.user_id,
            'user': user.to_dict(),
            'role': user.role,  
            'access_token': access_token
        }), 200  # 200 = OK
        
    except (ValidationException, AuthenticationException) as e:
        return jsonify(e.to_dict()), 401  # 401 = Unauthorized
    
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({
            'error': 'LoginError',
            'message': 'An error occurred during login'
        }), 500


# ============== GET PROFILE ==============
@bp.route('/profile', methods=['GET'])
@jwt_required()  # This decorator checks that valid token is provided
def get_profile():
    """
    Get current logged-in user's profile
    
    Requires: Authorization header with Bearer token
    
    Response:
    {
        "user_id": 1,
        "email": "user@example.com",
        ... other user data ...
        "loyalty": { ... loyalty info ... }
    }
    """
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Fetch user from database
        user = User.query.get(user_id)
        
        if not user:
            raise UserNotFoundException(user_id)
        
        # Get loyalty information
        loyalty = LoyaltyPoints.query.filter_by(user_id=user_id).first()
        
        # Prepare response data
        user_data = user.to_dict()
        
        if loyalty:
            user_data['loyalty'] = loyalty.to_dict()
        
        return jsonify(user_data), 200
        
    except UserNotFoundException as e:
        return jsonify(e.to_dict()), 404  # 404 = Not Found
    
    except Exception as e:
        print(f"❌ Profile error: {str(e)}")
        return jsonify({
            'error': 'ProfileError',
            'message': 'An error occurred fetching profile'
        }), 500


# ============== UPDATE PROFILE ==============
@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update current user's profile
    
    Requires: Authorization header with Bearer token
    
    Request (PUT):
    {
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "+9876543210"
    }
    
    Response:
    {
        "message": "Profile updated successfully",
        "user": { ... updated user data ... }
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        
        # Update fields if provided in request
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        
        if 'phone' in data:
            user.phone = data['phone']
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except UserNotFoundException as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 404
    
    except ValidationException as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Update profile error: {str(e)}")
        return jsonify({
            'error': 'UpdateError',
            'message': 'An error occurred updating profile'
        }), 500


# ============== CHANGE PASSWORD ==============
@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    
    Requires: Authorization header with Bearer token
    
    Request (POST):
    {
        "current_password": "oldpassword123",
        "new_password": "newpassword456"
    }
    
    Response:
    {
        "message": "Password changed successfully"
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            raise ValidationException("Current and new password are required")
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        
        # Verify current password
        if not user.verify_password(data['current_password']):
            raise AuthenticationException("Current password is incorrect")
        
        # Validate new password
        if len(data['new_password']) < 8:
            raise ValidationException(
                "New password must be at least 8 characters", 
                field="new_password"
            )
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except (ValidationException, AuthenticationException, UserNotFoundException) as e:
        db.session.rollback()
        return jsonify(e.to_dict()), 400
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Change password error: {str(e)}")
        return jsonify({
            'error': 'PasswordChangeError',
            'message': 'An error occurred changing password'
        }), 500
    
@bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Debug: Check who you are"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({
        'user_id': user_id,
        'email': user.email,
        'role': user.role,
        'full_name': user.full_name
    }), 200
