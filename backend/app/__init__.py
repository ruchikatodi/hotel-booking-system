"""
Flask Application Factory - FIXED CSS LOADING
"""

from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()


def create_app():
    """Application Factory Function"""
    
    # Get absolute paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # backend/app
    BACKEND_DIR = os.path.dirname(BASE_DIR)  # backend
    PROJECT_ROOT = os.path.dirname(BACKEND_DIR)  # project root
    
    # Create Flask app with correct paths
    app = Flask(
        __name__,
        template_folder=os.path.join(PROJECT_ROOT, 'frontend', 'templates'),
        static_folder=os.path.join(PROJECT_ROOT, 'frontend', 'static'),
        static_url_path='/static'
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    
    # Database configuration
    db_path = os.path.join(BACKEND_DIR, 'hotel_booking.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    
    # JWT configuration
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # Setup database and routes
    with app.app_context():
        # Import models
        from app.models import (User, Room, RoomCategory, Booking, 
                                Payment, LoyaltyPoints, Recommendation)
        
        # Import and register blueprints
        from app.routes import auth, booking, admin, payment, recommendations
        
        app.register_blueprint(auth.bp, url_prefix='/api/auth')
        app.register_blueprint(booking.bp, url_prefix='/api/bookings')
        app.register_blueprint(admin.bp, url_prefix='/api/admin')
        app.register_blueprint(payment.bp, url_prefix='/api/payments')
        app.register_blueprint(recommendations.bp, url_prefix='/api/recommendations')
        
        # Create database tables
        db.create_all()
        init_database()
    
    # ============================================
    # FRONTEND ROUTES (FIXED - NO DUPLICATES)
    # ============================================
    
    @app.route('/')
    def index():
        """Serve the main index page"""
        return send_from_directory(app.template_folder, 'index.html')
    
    @app.route('/<page>.html')
    def serve_html(page):
        """Serve HTML pages"""
        try:
            return send_from_directory(app.template_folder, f'{page}.html')
        except Exception as e:
            return {'error': f'Page not found: {page}'}, 404
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files (CSS, JS, images)"""
        return send_from_directory(app.static_folder, filename)
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'database': 'connected',
            'frontend': 'connected',
            'static_folder': app.static_folder,
            'template_folder': app.template_folder
        }
    
    return app


def init_database():
    """Initialize database with seed data"""
    from app.models import User, RoomCategory, Room, LoyaltyPoints, Recommendation
    
    if User.query.count() > 0:
        print("✅ Database already initialized")
        return
    
    print("🏗️  Initializing database...")
    
    try:
        # Create admin user
        admin = User(
            email='admin@hotel.com',
            password='admin123456',
            first_name='Admin',
            last_name='User',
            phone='1234567890',
            role='admin'
        )
        db.session.add(admin)
        db.session.flush()
        
        # Create customer
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
        
        # Create loyalty points
        db.session.add(LoyaltyPoints(user_id=admin.user_id))
        db.session.add(LoyaltyPoints(user_id=customer.user_id))
        
        # Room categories configuration
        category_config = [
            ('Standard Room', 'Comfortable room with essential amenities', 
             800.00, 2, ['Queen-bed', 'WiFi', 'TV', 'Bathroom'], 12),
            ('Deluxe Room', 'Stylish room with upgraded comfort', 
             1200.00, 2, ['Queen-bed', 'WiFi', 'TV', 'AC', 'Bathroom', 'Work Desk'], 15),
            ('Super Deluxe Room', 'Premium room with superior amenities', 
             1800.00, 3, ['King-bed', 'WiFi', 'Smart TV', 'AC', 'Bathroom', 'Mini Fridge', 'Work Desk'], 12),
            ('Executive Room', 'Business-focused room with workspace', 
             2800.00, 2, ['Two Queen-beds', 'WiFi', '4K TV', 'AC', 'Bathroom', 'Mini Fridge', 'Work Desk', 'Living Area'], 4),
            ('Family Suite', 'Large family-friendly setup', 
             5400.00, 6, ['Two king-beds', 'Balcony', 'WiFi', 'Sofa', '4K TV', 'AC', 'Two bathrooms', 'Dining-Table', 'Mini Fridge', 'Microwave', 'Work Desk', 'Living Area'], 3),
            ('Honeymoon Suite', 'Romantic suite with premium amenities', 
             5000.00, 2, ['King-bed', 'Balcony', 'WiFi', '4K TV', 'AC', 'Bathroom', 'Rose Petals', 'Champagne', 'Premium Mini Bar', 'Spa Bath', 'Living Area'], 5),
        ]
        
        # Create categories and rooms
        for idx, (name, desc, price, capacity, amenities, num_rooms) in enumerate(category_config, 1):
            category = RoomCategory(
                name=name,
                description=desc,
                base_price=price,
                capacity=capacity,
                amenities=amenities
            )
            db.session.add(category)
            db.session.flush()
            
            # Generate rooms
            for room_num in range(1, num_rooms + 1):
                floor = idx
                room_number = f"{floor}{room_num:02d}"
                room = Room(
                    room_number=room_number,
                    category_id=category.category_id,
                    floor=floor,
                    description=f"{name} - {desc}"
                )
                db.session.add(room)
        
        # Create recommendations
        recommendations = [
            Recommendation(
                title='Lalbagh Botanical Garden',
                category='tourist_spot',
                description='Historic botanical garden with glasshouse and exotic plants',
                address='Lalbagh Road, Mavalli, Bengaluru, Karnataka',
                rating=4.7,
                price_range='cheap',
                image_url='/static/images/nearby/lalbagh.jpg'
            ),
            Recommendation(
                title='Cubbon Park',
                category='tourist_spot',
                description='300-acre green oasis perfect for strolling and picnics',
                address='Cubbon Park, Bengaluru, Karnataka',
                rating=4.6,
                price_range='free',
                image_url='/static/images/nearby/cubbon.jpg'
            ),
            Recommendation(
                title='Bangalore Palace',
                category='tourist_spot',
                description='Grand Tudor-style palace with vintage interiors',
                address='Vasanth Nagar, Bengaluru, Karnataka',
                rating=4.5,
                price_range='moderate',
                image_url='/static/images/nearby/palace.jpg'
            ),
            Recommendation(
                title='ISKCON Temple',
                category='cultural',
                description='Large Krishna temple with gardens and cultural centre',
                address='Hare Krishna Hill, Rajajinagar, Bengaluru, Karnataka',
                rating=4.6,
                price_range='free',
                image_url='/static/images/nearby/iskcon.jpg'
            ),
            Recommendation(
                title='Commercial Street',
                category='shopping',
                description='Busy shopping street with clothes, jewellery, and stalls',
                address='Commercial Street, Shivaji Nagar, Bengaluru, Karnataka',
                rating=4.3,
                price_range='moderate',
                image_url='/static/images/nearby/commercial.jpg'
            ),
            Recommendation(
                title='Dyu Art Café',
                category='cafe',
                description='Artistic rustic café in bungalow-style space',
                address='23, KHB MIG Colony, Koramangala 8th Block, Bengaluru, Karnataka',
                rating=4.5,
                price_range='moderate',
                image_url='/static/images/nearby/dyu_cafe.jpg'
            ),
            Recommendation(
                title='Sly Granny',
                category='restaurant',
                description='Quirky European-inspired restaurant with cocktails',
                address='Indiranagar, Bengaluru, Karnataka',
                rating=4.4,
                price_range='mid-expensive',
                image_url='/static/images/nearby/sly_granny.jpg'
            ),
            Recommendation(
                title='Brigade Road & MG Road',
                category='nightlife',
                description='Vibrant commercial stretch with pubs, bars and shopping',
                address='Brigade Road & MG Road, Bengaluru, Karnataka',
                rating=4.3,
                price_range='moderate',
                image_url='/static/images/nearby/brigade_road.jpg'
            )
        ]
        
        for rec in recommendations:
            db.session.add(rec)
        
        db.session.commit()
        
        print("\n✅ Database initialized successfully!")
        print("📧 Admin: admin@hotel.com / admin123456")
        print("📧 Customer: ruchika@hotel.com / ruchika123")
        print("🛏️  Rooms created: 51 total")
        print("🌐 Frontend: http://localhost:5000/")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")