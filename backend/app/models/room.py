"""
Room Model
Represents individual rooms in the hotel
"""

from app import db
from datetime import datetime


class Room(db.Model):
    """
    Room Model - Represents a physical room
    
    Attributes:
    - room_id: Unique identifier
    - room_number: Room number (like "101", "202")
    - category_id: Which type of room (Standard, Deluxe, etc.)
    - floor: Which floor the room is on
    - status: Current status (available, occupied, maintenance, reserved)
    - description: Additional notes about the room
    """
    __tablename__ = 'rooms'
    
    room_id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('room_categories.category_id'), nullable=False)
    floor = db.Column(db.Integer)
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance, reserved
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = db.relationship('RoomCategory', back_populates='rooms')
    bookings = db.relationship('Booking', back_populates='room')
    
    # Status constants (so we don't hardcode strings everywhere)
    STATUS_AVAILABLE = 'available'
    STATUS_OCCUPIED = 'occupied'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_RESERVED = 'reserved'
    
    def __init__(self, room_number, category_id, floor, status='available', description=""):
        """Constructor"""
        self.room_number = room_number
        self.category_id = category_id
        self.floor = floor
        self.status = status
        self.description = description
    
    @property
    def is_available(self):
        """Check if room is available for booking"""
        return self.status == 'available'
    
    def set_status(self, new_status):
        """Change room status"""
        if new_status not in [self.STATUS_AVAILABLE, self.STATUS_OCCUPIED, 
                             self.STATUS_MAINTENANCE, self.STATUS_RESERVED]:
            raise ValueError(f"Invalid status: {new_status}")
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_category=True):
        """Convert to dictionary"""
        data = {
            'room_id': self.room_id,
            'room_number': self.room_number,
            'floor': self.floor,
            'status': self.status,
            'description': self.description,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_category and self.category:
            data['category'] = self.category.to_dict()
        else:
            data['category_id'] = self.category_id
        
        return data
    
    def __repr__(self):
        return f"<Room {self.room_number} - {self.status}>"