"""
Flask Application Factory - AUTO ROOM GENERATION
This initializes and configures the Flask app with smart room generation
Instead of hardcoding room numbers, just specify count per category!
"""

from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()  # Database
jwt = JWTManager()  # JWT for authentication
mail = Mail()  # Email sending


def create_app():
    """
    Application Factory Function
    """
    
    # Create the Flask app with correct paths for frontend
    app = Flask(__name__)

    # THIS IS THE 100% WORKING VERSION FOR YOUR CURRENT FOLDER STRUCTURE
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))           # → backend/app
    PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))       # → main project folder

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '../../frontend/templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '../../frontend/static'),
        static_url_path='/static'
    )
    # Set configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    
    # Database configuration - SQLite
    db_path = os.path.join(os.path.dirname(__file__), '../hotel_booking.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration (optional)
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    
    # JWT configuration
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Initialize extensions with the app
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)  # Allow requests from frontend
    
    # Context for database operations
    with app.app_context():
        # Import all models so they're registered with SQLAlchemy
        from app.models import (User, Room, RoomCategory, Booking, 
                                Payment, LoyaltyPoints, Recommendation)
        
        # Import and register blueprints (route modules)
        from app.routes import auth, booking, admin, payment, recommendations
        
        # Register blueprints with URL prefixes for API
        app.register_blueprint(auth.bp, url_prefix='/api/auth')
        app.register_blueprint(booking.bp, url_prefix='/api/bookings')
        app.register_blueprint(admin.bp, url_prefix='/api/admin')
        app.register_blueprint(payment.bp, url_prefix='/api/payments')
        app.register_blueprint(recommendations.bp, url_prefix='/api/recommendations')
        
        # Create all database tables if they don't exist
        db.create_all()
        
        # Initialize database with seed data (only on first run)
        init_database()
    
    # ============================================
    # FRONTEND ROUTES
    # ============================================
    
    # Home page - serve index.html
    @app.route('/')
    def index():
        try:
            return send_from_directory(
                os.path.join(os.path.dirname(__file__), '../../frontend/templates'),
                'index.html'
            )
        except Exception as e:
            print(f"❌ Error serving index.html: {e}")
            return {
                'message': '🏨 Hotel Booking System API',
                'status': 'running',
                'version': '1.0.0',
                'error': 'Frontend files not found in templates folder'
            }, 200
    
    # Serve HTML pages
    @app.route('/<page>.html')
    def serve_html(page):
        try:
            return send_from_directory(
                os.path.join(os.path.dirname(__file__), '../../frontend/templates'),
                f'{page}.html'
            )
        except Exception as e:
            print(f"❌ Error serving {page}.html: {e}")
            return {'error': f'Page {page} not found'}, 404
    
    # Serve static files (CSS, JS, Images)
    @app.route('/static/<path:path>')
    def serve_static(path):
        try:
            return send_from_directory(
                os.path.join(os.path.dirname(__file__), '../../frontend/static'),
                path
            )
        except Exception as e:
            print(f"❌ Error serving static file {path}: {e}")
            return {'error': 'Static file not found'}, 404
    
    # Health check route
    @app.route('/health')
    def health():
        return {
            'status': 'healthy',
            'database': 'sqlite',
            'frontend': 'connected'
        }
    # Serve frontend static files
    @app.route('/')
    @app.route('/index.html')
    def serve_index():
        from flask import send_from_directory
        return send_from_directory('../../frontend/templates', 'index.html')
    
    @app.route('/<path:path>')
    def serve_frontend(path):
        from flask import send_from_directory
        if path.endswith('.html'):
            return send_from_directory('../../frontend/templates', path)
        return send_from_directory('../../frontend/static', path)
    return app


def init_database():
    """
    Initialize database with sample data on first run
    This runs only once (when database is empty)
    
    NEW: Auto-generates rooms based on category count!
    """
    from app.models import User, RoomCategory, Room, LoyaltyPoints, Recommendation
    
    # Check if data already exists
    if User.query.count() > 0:
        print("✅ Database already initialized")
        return
    
    print("🏗️  Initializing database with seed data...")
    
    try:
        # ============================================
        # CREATE USERS
        # ============================================
        
        # Create admin user
        admin_user = User(
            email='admin@hotel.com',
            password='admin123456',
            first_name='Admin',
            last_name='User',
            phone='1234567890',
            role='admin'
        )
        db.session.add(admin_user)
        db.session.flush()  # Get the user_id
        
        # Create test customer
        customer = User(
            email='ruchika@hotel.com',
            password='ruchika123',
            first_name='Ruchika',
            last_name='Todi',
            phone='9775270513',
            role='customer'
        )
        db.session.add(customer)
        db.session.flush()
        
        # Create loyalty points for users
        admin_loyalty = LoyaltyPoints(user_id=admin_user.user_id)
        customer_loyalty = LoyaltyPoints(user_id=customer.user_id)
        db.session.add(admin_loyalty)
        db.session.add(customer_loyalty)
        
        # ============================================
        # CREATE ROOM CATEGORIES
        # ============================================
        
        # Define categories with room count
        # Format: (name, description, base_price, capacity, amenities, num_rooms)
        category_config = [
            (
                'Standard Room',
                'A comfortable room with essential amenities for budget-conscious travelers.',
                800.00,
                2,
                ['Queen-bed', 'WiFi', 'TV', 'Bathroom'],
                12  # Create 12 Standard rooms
            ),
            (
                'Deluxe Room',
                'A stylish, well-furnished room offering added space and upgraded comfort',
                1200.00,
                2,
                ['Queen-bed', 'WiFi', 'TV', 'AC', 'Bathroom', 'Work Desk'],
                15  
            ),
            (
                'Super Deluxe Room',
                'A premium room with enhanced interiors and superior amenities for a luxurious stay.',
                1800.00,
                3,
                ['King-bed', 'WiFi', 'Smart TV', 'AC', 'Bathroom', 'Mini Fridge', 'Work Desk'],
                12  
            ),
            (
                'Executive Room',
                'A business-focused room featuring a dedicated workspace and premium utilities',
                2800.00,
                2,
                ['Two Queen-beds', 'WiFi', '4K TV', 'AC', 'Bathroom','Mini Fridge', 'Work Desk', 'Living Area'],
                4  
            ),
            (
                'Family Suite',
                'A large, family-friendly setup with multiple rooms designed for group stays',
                5400.00,
                6,
                ['Two king-beds', 'Balcony' ,'WiFi', 'Sofa', '4K TV', 'AC', 'Two bathrooms', 'Dining-Table', 'Mini Fridge', 'Microwave', 'Work Desk', 'Living Area'],
                3  # Create 3 Suites
            ),
            (
                'Honeymoon Suite',
                'A top-tier, opulent romantic suite offering the highest level of comfort, space, and personalized services',
                5000.00,
                2,
                ['King-bed', 'Balcony', 'WiFi', '4K TV', 'AC', 'Bathroom', 'Rose Petals', 'Champagne','Premium Mini Bar', 'Spa Bath', 'Living Area'],
                5 # Create 5 Honeymoon Suites
            ),
        ]
        
        # Create categories and rooms
        total_rooms = 0
        room_count_by_category = {}
        
        for idx, (name, description, price, capacity, amenities, num_rooms) in enumerate(category_config, 1):
            # Create category
            category = RoomCategory(
                name=name,
                description=description,
                base_price=price,
                capacity=capacity,
                amenities=amenities
            )
            db.session.add(category)
            db.session.flush()  # Get category_id
            
            # ============================================
            # AUTO-GENERATE ROOMS FOR THIS CATEGORY
            # ============================================
            
            rooms_created = 0
            
            for room_num in range(1, num_rooms + 1):
                # Generate room number based on floor and sequence
                # Format: 100s = Floor 1, 200s = Floor 2, etc.
                floor = idx  # Use category index as floor
                room_number = f"{floor}{room_num:02d}"  # e.g., 101, 102, 201, 202, etc.
                
                room = Room(
                    room_number=room_number,
                    category_id=category.category_id,
                    floor=floor,
                    description=f"{name} - {description}"
                )
                db.session.add(room)
                rooms_created += 1
            
            total_rooms += rooms_created
            room_count_by_category[name] = rooms_created
        
        db.session.commit()
        
        # ============================================
        # CREATE RECOMMENDATIONS
        # ============================================
        
        recommendations = [
            Recommendation(
                title='Lalbagh Botanical Garden',  
                category='tourist_spot',  
                description='Historic and sprawling botanical garden with a beautiful glasshouse, lakes and exotic plant species',  
                address='Lalbagh Road, Mavalli, Bengaluru, Karnataka',  
                rating=4.7,  
                price_range='cheap'
            ),
            Recommendation(
                title='Cubbon Park',  
                category='tourist_spot',  
                description='A lush 300-acre green oasis in the heart of the city, perfect for strolling, picnics, and relaxing',  
                address='Cubbon Park, Bengaluru, Karnataka',  
                rating=4.6,  
                price_range='free'
            ),
            Recommendation(
                title='Bangalore Palace',  
                category='tourist_spot',  
                description='Grand Tudor-style palace with ornate woodwork, vintage interiors, and royal history',  
                address='Vasanth Nagar, Bengaluru, Karnataka',  
                rating=4.5,  
                price_range='moderate'
            ),
            Recommendation(
                title='ISKCON Temple Bangalore',  
                category='cultural',  
                description='Large Krishna temple complex with gardens, a cultural centre, and vegetarian restaurant',  
                address='Hare Krishna Hill, Chord Road, Rajajinagar, Bengaluru, Karnataka',  
                rating=4.6,  
                price_range='free'
            ),
            Recommendation(
                'Commercial Street',  
                category='shopping',  
                description='One of Bangalore busiest shopping streets clothes, jewellery, antiques, local street stalls',  
                address='Commercial Street, Shivaji Nagar, Bengaluru, Karnataka',  
                rating=4.3,  
                price_range='moderate'
            ),
            Recommendation(
                title='Dyu Art Café',  
                category='cafe',  
                description='Artistic, rustic café in a bungalow-style space, great for quiet conversations or working',  
                address='23, KHB MIG Colony, Koramangala 8th Block, Bengaluru, Karnataka',  
                rating=4.5,  
                price_range='moderate'
            ),
            Recommendation(
                title='Sly Granny',  
                category='restaurant',  
                description='Quirky European-inspired restaurant with an artistic twist and cocktails',  
                address='Indiranagar, Bengaluru, Karnataka',
                rating=4.4,  
                price_range='mid-expensive'
            ),
            Recommendation(
                title='Brigade Road & MG Road',  
                category='nightlife',  
                description='Vibrant commercial stretch famous for boutiques, pubs, bars and street shopping',  
                address='Brigade Road & MG Road, Bengaluru, Karnataka',  
                rating=4.3,  
                price_range='moderate'
            )
        ]
        for rec in recommendations:
            db.session.add(rec)
        
        db.session.commit()
        
        # ============================================
        # PRINT INITIALIZATION SUMMARY
        # ============================================
        
        print("\n✅ Database initialized successfully!\n")
        print("👥 USERS:")
        print(f"   📧 Admin user: admin@hotel.com / admin123456")
        print(f"   📧 Customer user: ruchika@hotel.com / ruchika123\n")
        
        print("🛏️  ROOMS CREATED (Auto-Generated):")
        for category_name, count in room_count_by_category.items():
            print(f"   {category_name}: {count} rooms")
        print(f"   ➜ Total: {total_rooms} rooms\n")
        
        print("🎯 CATEGORIES CREATED: 6")
        print("🌟 RECOMMENDATIONS CREATED: 8 (Clean version - no extra fields)\n")
        
        print("🌐 FRONTEND URLs:")
        print(f"   Homepage: http://localhost:5000/")
        print(f"   Login: http://localhost:5000/login.html")
        print(f"   Register: http://localhost:5000/register.html")
        print(f"   Admin: http://localhost:5000/dashboard-admin.html\n")
        
        print("🔌 API ENDPOINTS:")
        print(f"   Rooms: http://localhost:5000/api/bookings/search")
        print(f"   Categories: http://localhost:5000/api/bookings/categories")
        print(f"   Recommendations: http://localhost:5000/api/recommendations\n")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error initializing database: {e}")


# ============================================
# HOW TO CUSTOMIZE
# ============================================

"""
TO ADD MORE CATEGORIES OR CHANGE ROOM COUNT:

1. Edit the category_config list in init_database()

2. Format: (name, description, price, capacity, amenities, num_rooms)

3. Example - Add a new category:
   (
       'Villa',
       'Luxurious standalone villa with pool',
       1000.00,
       6,
       ['Pool', 'Garden', 'Kitchen', 'WiFi', '4K TV'],
       2  # Create 2 villas
   ),

4. The system will automatically create rooms:
   - Villa 1: Room 601, 602
   - Each villa gets floor 6 (6th category)
   - Names auto-generated as XXY format
     where XX = floor, Y = sequence number

5. Delete hotel_booking.db and restart Flask to apply changes

ROOM NUMBERING SYSTEM:
- 100-109: Floor 1 (Category 1) - Economy Rooms
- 200-208: Floor 2 (Category 2) - Standard Rooms
- 300-305: Floor 3 (Category 3) - Deluxe Rooms
- 400-402: Floor 4 (Category 4) - Suites
- 500-501: Floor 5 (Category 5) - Honeymoon Suites
- 600+: Floor 6+ (Additional categories)

BENEFITS:
✅ Easy to add/remove categories
✅ Automatic room numbering
✅ No hardcoding room numbers
✅ Scalable to any number of rooms
✅ Clean and maintainable code
"""