"""Business models for room booking system."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from .database import Database


class Room:
    """Meeting room model."""

    def __init__(self, name: str, capacity: int, db: Database):
        """Initialize room."""
        self.name = name
        self.capacity = capacity
        self.db = db

    @classmethod
    def create(cls, name: str, capacity: int, db: Database) -> 'Room':
        """Create a new room in the database."""
        db.add_room(name, capacity)
        return cls(name, capacity, db)

    @classmethod
    def get(cls, name: str, db: Database) -> Optional['Room']:
        """Get room by name from database."""
        room_data = db.get_room(name)
        if room_data:
            return cls(
                name=room_data['name'],
                capacity=room_data['capacity'],
                db=db
            )
        return None

    @classmethod
    def get_all(cls, db: Database) -> List['Room']:
        """Get all rooms from database."""
        rooms_data = db.get_all_rooms()
        return [
            cls(name=r['name'], capacity=r['capacity'], db=db)
            for r in rooms_data
        ]

    def is_available(self, start_time: str, end_time: str) -> bool:
        """Check if room is available for given time range."""
        conflict = self.db.check_booking_conflict(
            self.name,
            start_time,
            end_time
        )
        return conflict is None

    def get_current_booking(self, current_time: datetime) -> Optional['Booking']:
        """Get current booking for this room."""
        bookings = self.db.get_room_bookings(self.name)
        current_time_str = current_time.isoformat()

        for booking_data in bookings:
            if (booking_data['start_time'] <= current_time_str < booking_data['end_time']):
                return Booking.from_dict(booking_data, self.db)

        return None

    def get_all_bookings(self) -> List['Booking']:
        """Get all bookings for this room."""
        bookings_data = self.db.get_room_bookings(self.name)
        return [Booking.from_dict(b, self.db) for b in bookings_data]

    def __repr__(self) -> str:
        """String representation."""
        return f"Room(name='{self.name}', capacity={self.capacity})"


class Booking:
    """Room booking model."""

    def __init__(
        self,
        room_name: str,
        user_id: int,
        username: str,
        start_time: str,
        end_time: str,
        db: Database,
        booking_id: Optional[int] = None
    ):
        """Initialize booking."""
        self.id = booking_id
        self.room_name = room_name
        self.user_id = user_id
        self.username = username
        self.start_time = start_time
        self.end_time = end_time
        self.db = db

    @classmethod
    def create(
        cls,
        room_name: str,
        user_id: int,
        username: str,
        start_time: str,
        end_time: str,
        db: Database
    ) -> Optional['Booking']:
        """Create a new booking in the database.

        Returns None if there's a conflict.
        """
        # Check for conflicts
        conflict = db.check_booking_conflict(room_name, start_time, end_time)
        if conflict:
            return None

        # Create booking
        booking_id = db.create_booking(
            room_name, user_id, username, start_time, end_time
        )

        return cls(
            room_name=room_name,
            user_id=user_id,
            username=username,
            start_time=start_time,
            end_time=end_time,
            db=db,
            booking_id=booking_id
        )

    @classmethod
    def get(cls, booking_id: int, db: Database) -> Optional['Booking']:
        """Get booking by ID from database."""
        booking_data = db.get_booking(booking_id)
        if booking_data:
            return cls.from_dict(booking_data, db)
        return None

    @classmethod
    def get_user_bookings(cls, user_id: int, db: Database) -> List['Booking']:
        """Get all bookings for a user."""
        bookings_data = db.get_user_bookings(user_id)
        return [cls.from_dict(b, db) for b in bookings_data]

    @classmethod
    def from_dict(cls, data: Dict[str, Any], db: Database) -> 'Booking':
        """Create booking instance from dictionary."""
        return cls(
            room_name=data['room_name'],
            user_id=data['user_id'],
            username=data['username'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            db=db,
            booking_id=data['id']
        )

    def delete(self) -> bool:
        """Delete this booking."""
        if self.id is None:
            return False
        return self.db.delete_booking(self.id)

    def is_owner(self, user_id: int) -> bool:
        """Check if user is the owner of this booking."""
        return self.user_id == user_id

    def is_active(self, current_time: datetime) -> bool:
        """Check if booking is currently active."""
        current_time_str = current_time.isoformat()
        return self.start_time <= current_time_str < self.end_time

    def get_end_time_formatted(self) -> str:
        """Get formatted end time for display."""
        try:
            dt = datetime.fromisoformat(self.end_time)
            return dt.strftime("%H:%M")
        except ValueError:
            return self.end_time

    def __repr__(self) -> str:
        """String representation."""
        return (f"Booking(id={self.id}, room='{self.room_name}', "
                f"user='{self.username}', {self.start_time} - {self.end_time})")
