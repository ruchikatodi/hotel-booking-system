"""
Recommendation Model
Simplified version containing only id, title, description, image_url, and google_maps_url
"""

from app import db


class Recommendation(db.Model):
    """
    Recommendation Model - Nearby attractions/spots
    
    Attributes:
    - recommendation_id: Unique identifier (PK)
    - title: Name of the spot
    - description: Description detailing what the spot is
    - image_url: Custom image URL or local path
    - google_maps_url: Custom Google Maps link
    """
    __tablename__ = 'recommendations'
    
    recommendation_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    google_maps_url = db.Column(db.String(500))
    
    def __init__(self, title, description, image_url=None, google_maps_url=None):
        """Constructor"""
        self.title = title
        self.description = description
        self.image_url = image_url
        self.google_maps_url = google_maps_url
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'recommendation_id': self.recommendation_id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'google_maps_url': self.google_maps_url
        }
    
    def __repr__(self):
        return f"<Recommendation #{self.recommendation_id} - {self.title}>"