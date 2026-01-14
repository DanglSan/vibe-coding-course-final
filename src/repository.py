"""Repository pattern for data access."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from .database import Database


class RoomRepository(ABC):
    """Abstract repository for room data access."""

    @abstractmethod
    def add_room(self, name: str, capacity: int) -> int:
        """Add a new room."""
        pass

    @abstractmethod
    def get_room(self, name: str) -> Optional[Dict[str, Any]]:
        """Get room by name."""
        pass

    @abstractmethod
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Get all rooms."""
        pass

    @abstractmethod
    def create_booking(
        self,
        room_name: str,
        user_id: int,
        username: str,
        start_time: str,
        end_time: str
    ) -> int:
        """Create a new booking."""
        pass

    @abstractmethod
    def get_booking(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Get booking by ID."""
        pass

    @abstractmethod
    def get_room_bookings(self, room_name: str) -> List[Dict[str, Any]]:
        """Get all bookings for a room."""
        pass

    @abstractmethod
    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a user."""
        pass

    @abstractmethod
    def delete_booking(self, booking_id: int) -> bool:
        """Delete a booking by ID."""
        pass

    @abstractmethod
    def delete_room_bookings(self, room_name: str) -> int:
        """Delete all bookings for a room."""
        pass

    @abstractmethod
    def find_booking_by_room_and_user(
        self,
        room_name: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Find active booking for a room by specific user."""
        pass

    @abstractmethod
    def check_booking_conflict(
        self,
        room_name: str,
        start_time: str,
        end_time: str
    ) -> Optional[Dict[str, Any]]:
        """Check if there's a booking conflict for given time range."""
        pass

    @abstractmethod
    def add_admin(self, user_id: int, username: str) -> None:
        """Add user as admin."""
        pass

    @abstractmethod
    def remove_admin(self, user_id: int) -> None:
        """Remove user from admins."""
        pass

    @abstractmethod
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        pass

    @abstractmethod
    def get_all_admins(self) -> List[Dict[str, Any]]:
        """Get list of all admins."""
        pass


class SQLiteRepository(RoomRepository):
    """SQLite implementation of room repository."""

    def __init__(self, db_path: str = "bookings.db"):
        """Initialize with SQLite database."""
        self.db = Database(db_path)

    def add_room(self, name: str, capacity: int) -> int:
        return self.db.add_room(name, capacity)

    def get_room(self, name: str) -> Optional[Dict[str, Any]]:
        return self.db.get_room(name)

    def get_all_rooms(self) -> List[Dict[str, Any]]:
        return self.db.get_all_rooms()

    def create_booking(
        self,
        room_name: str,
        user_id: int,
        username: str,
        start_time: str,
        end_time: str
    ) -> int:
        return self.db.create_booking(room_name, user_id, username, start_time, end_time)

    def get_booking(self, booking_id: int) -> Optional[Dict[str, Any]]:
        return self.db.get_booking(booking_id)

    def get_room_bookings(self, room_name: str) -> List[Dict[str, Any]]:
        return self.db.get_room_bookings(room_name)

    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        return self.db.get_user_bookings(user_id)

    def delete_booking(self, booking_id: int) -> bool:
        return self.db.delete_booking(booking_id)

    def delete_room_bookings(self, room_name: str) -> int:
        return self.db.delete_room_bookings(room_name)

    def find_booking_by_room_and_user(
        self,
        room_name: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        return self.db.find_booking_by_room_and_user(room_name, user_id)

    def check_booking_conflict(
        self,
        room_name: str,
        start_time: str,
        end_time: str
    ) -> Optional[Dict[str, Any]]:
        return self.db.check_booking_conflict(room_name, start_time, end_time)

    def add_admin(self, user_id: int, username: str) -> None:
        self.db.add_admin(user_id, username)

    def remove_admin(self, user_id: int) -> None:
        self.db.remove_admin(user_id)

    def is_admin(self, user_id: int) -> bool:
        return self.db.is_admin(user_id)

    def get_all_admins(self) -> List[Dict[str, Any]]:
        return self.db.get_all_admins()


class InMemoryRepository(RoomRepository):
    """In-memory implementation of room repository for testing."""

    def __init__(self):
        """Initialize with empty in-memory storage."""
        self.rooms: Dict[str, Dict[str, Any]] = {}
        self.bookings: Dict[int, Dict[str, Any]] = {}
        self.admins: Dict[int, Dict[str, Any]] = {}  # user_id -> admin details
        self.next_room_id = 1
        self.next_booking_id = 1

    def add_room(self, name: str, capacity: int) -> int:
        """Add a new room."""
        room_id = self.next_room_id
        self.next_room_id += 1
        self.rooms[name] = {
            'id': room_id,
            'name': name,
            'capacity': capacity
        }
        return room_id

    def get_room(self, name: str) -> Optional[Dict[str, Any]]:
        """Get room by name."""
        return self.rooms.get(name)

    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Get all rooms."""
        return sorted(self.rooms.values(), key=lambda r: r['name'])

    def create_booking(
        self,
        room_name: str,
        user_id: int,
        username: str,
        start_time: str,
        end_time: str
    ) -> int:
        """Create a new booking."""
        booking_id = self.next_booking_id
        self.next_booking_id += 1
        self.bookings[booking_id] = {
            'id': booking_id,
            'room_name': room_name,
            'user_id': user_id,
            'username': username,
            'start_time': start_time,
            'end_time': end_time,
            'created_at': datetime.now().isoformat()
        }
        return booking_id

    def get_booking(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Get booking by ID."""
        return self.bookings.get(booking_id)

    def get_room_bookings(self, room_name: str) -> List[Dict[str, Any]]:
        """Get all bookings for a room."""
        result = [
            b for b in self.bookings.values()
            if b['room_name'] == room_name
        ]
        return sorted(result, key=lambda b: b['start_time'])

    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a user."""
        result = [
            b for b in self.bookings.values()
            if b['user_id'] == user_id
        ]
        return sorted(result, key=lambda b: b['start_time'])

    def delete_booking(self, booking_id: int) -> bool:
        """Delete a booking by ID."""
        if booking_id in self.bookings:
            del self.bookings[booking_id]
            return True
        return False

    def delete_room_bookings(self, room_name: str) -> int:
        """Delete all bookings for a room."""
        to_delete = [
            bid for bid, b in self.bookings.items()
            if b['room_name'] == room_name
        ]
        for bid in to_delete:
            del self.bookings[bid]
        return len(to_delete)

    def find_booking_by_room_and_user(
        self,
        room_name: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Find active booking for a room by specific user."""
        bookings = [
            b for b in self.bookings.values()
            if b['room_name'] == room_name and b['user_id'] == user_id
        ]
        if bookings:
            # Return most recent booking
            return sorted(bookings, key=lambda b: b['start_time'], reverse=True)[0]
        return None

    def check_booking_conflict(
        self,
        room_name: str,
        start_time: str,
        end_time: str
    ) -> Optional[Dict[str, Any]]:
        """Check if there's a booking conflict for given time range."""
        for booking in self.bookings.values():
            if booking['room_name'] != room_name:
                continue

            # Check for overlap
            # Overlap happens when:
            # - new booking starts during existing booking
            # - new booking ends during existing booking
            # - new booking completely contains existing booking
            if (
                (booking['start_time'] < end_time and booking['end_time'] > start_time) or
                (start_time >= booking['start_time'] and start_time < booking['end_time']) or
                (end_time > booking['start_time'] and end_time <= booking['end_time'])
            ):
                return booking

        return None

    def add_admin(self, user_id: int, username: str) -> None:
        """Add user as admin."""
        self.admins[user_id] = {
            'user_id': user_id,
            'username': username,
            'added_at': datetime.now().isoformat()
        }

    def remove_admin(self, user_id: int) -> None:
        """Remove user from admins."""
        self.admins.pop(user_id, None)

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in self.admins

    def get_all_admins(self) -> List[Dict[str, Any]]:
        """Get list of all admins."""
        return sorted(self.admins.values(), key=lambda a: a['added_at'])
