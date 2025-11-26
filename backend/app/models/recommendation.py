"""
Recommendation Model
Places to visit near the hotel (cafes, restaurants, tourist spots, etc.)
"""

from app import db
from datetime import datetime


class Recommendation(db.Model):
    """
    Recommendation Model - Places to visit near the hotel
    
    Attributes:
    - title: Name of the place
    - category: Type (cafe, restaurant, tourist_spot, shopping, etc.)
    - description: What's special about it
    - rating: Star rating (1-5)
    - distance_from_hotel: Distance in kilometers
    """
    __tablename__ = 'recommendations'
    
    recommendation_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    rating = db.Column(db.Float, default=0)  # 1-5 stars
    price_range = db.Column(db.String(20), default='moderate')  # budget, moderate, expensive
    distance_from_hotel = db.Column(db.Float)  # in km
    contact_info = db.Column(db.String(100))
    website = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Category constants
    CATEGORY_CAFE = 'cafe'
    CATEGORY_RESTAURANT = 'restaurant'
    CATEGORY_TOURIST_SPOT = 'tourist_spot'
    CATEGORY_SHOPPING = 'shopping'
    CATEGORY_NIGHTLIFE = 'nightlife'
    CATEGORY_CULTURAL = 'cultural'
    
    def __init__(self, title, category, description, address, rating=0, price_range="moderate"):
        """Constructor"""
        self.title = title
        self.category = category
        self.description = description
        self.address = address
        self.rating = rating
        self.price_range = price_range
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'recommendation_id': self.recommendation_id,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'rating': self.rating,
            'price_range': self.price_range,
            'distance_from_hotel': self.distance_from_hotel,
            'contact_info': self.contact_info,
            'website': self.website,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<Recommendation {self.title} ({self.category}) - ⭐{self.rating}>"