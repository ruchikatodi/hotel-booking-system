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
                description='A historic 240-acre botanical garden in Bengaluru featuring a famous 19th-century Glass House, serene lake, and over 1,800 species of tropical plants.',
                image_url='/static/images/lalbagh.jpg',
                google_maps_url='https://maps.app.goo.gl/6qozp1mPpF9BGeaH8?g_st=aw'            
            ),
            Recommendation(
                title='Cubbon Park',
                description='A massive 300-acre green oasis in the heart of the city, perfect for morning walks, quiet reading, picnics, and exploring historic libraries and museums.',
                image_url='/static/images/cubbon.webp',
                google_maps_url='https://maps.app.goo.gl/yXfJGUDRZv1uZRzw5?g_st=aw'
            ),
            Recommendation(
                title='Bangalore Palace',
                description='A majestic royal palace built in the late 19th century, featuring Tudor-style architecture, beautiful wood carvings, vintage furniture, and historical photos.',
                image_url='/static/images/palace.webp',
                google_maps_url='https://maps.app.goo.gl/Lbkp7rJhV6rk73zX8?g_st=aw'
            ),
            Recommendation(
                title='ISKCON Temple',
                description='A grand neo-classical Krishna temple and cultural complex situated on a hillock, known for its spiritual atmosphere, beautiful architecture, and delicious prasadam.',
                image_url='/static/images/iskcon.jpg',
                google_maps_url='https://maps.app.goo.gl/S1Sj3a8vLwb9uD1m6?g_st=aw'
            ),
            Recommendation(
                title='Commercial Street',
                description='A vibrant and bustling shopping street famous for its wide variety of clothing, footwear, jewellery, street food, and lively local bazaar atmosphere.',
                image_url='/static/images/commercial.webp',
                google_maps_url='https://maps.app.goo.gl/hm9PQZnY2YmK5T7k6?g_st=aw'
            ),
            Recommendation(
                title='Dyu Art Café',
                description='A charming, artistic café housed in a traditional bungalow, offering a rustic courtyard setting, delicious continental snacks, coffee, and local art displays.',
                image_url='/static/images/dyu_cafe.avif',
                google_maps_url='https://maps.app.goo.gl/Y7gDcSoxQsYUxe218?g_st=aw'
            ),
            Recommendation(
                title='Sly Granny',
                description='A quirky, multi-story European restaurant and lounge featuring eccentric decor, a rooftop bar, artisanal cocktails, and a modern global menu.',
                image_url='/static/images/sly.avif',
                google_maps_url='https://maps.app.goo.gl/rNpF6UdCy4aQWy7WA?g_st=aw'
            ),
            Recommendation(
                title='Brigade Road & MG Road',
                description='One of the city\'s most energetic commercial hubs, lined with popular retail outlets, cafes, restaurants, pubs, and vibrant nightlife venues.',
                image_url='/static/images/church_street.webp',
                google_maps_url='https://maps.app.goo.gl/rNpF6UdCy4aQWy7WA?g_st=aw'
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