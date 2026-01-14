"""Business logic service for room booking."""
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from .repository import RoomRepository


class RoomBookingService:
    """Service layer with all business logic for room booking."""

    def __init__(self, repository: RoomRepository):
        """Initialize service with a repository."""
        self.repo = repository

    def _parse_time_range(self, time_range: str) -> tuple[datetime, datetime]:
        """Parse time range string to datetime objects.

        Args:
            time_range: Time range in format "HH:MM-HH:MM"

        Returns:
            Tuple of (start_time, end_time) as datetime objects

        Raises:
            ValueError: If time format is invalid
        """
        # Parse time range format
        match = re.match(r'^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$', time_range)
        if not match:
            raise ValueError("Неверный формат времени. Используйте HH:MM-HH:MM")

        start_str = match.group(1)
        end_str = match.group(2)

        # Convert to datetime
        today = datetime.now().date()
        try:
            start_time = datetime.strptime(f"{today} {start_str}", "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(f"{today} {end_str}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            raise ValueError(f"Неверный формат времени: {e}")

        if start_time >= end_time:
            raise ValueError("Время начала должно быть раньше времени окончания")

        return start_time, end_time

    def list_all_rooms(self) -> List[Dict[str, Any]]:
        """Get list of all rooms."""
        return self.repo.get_all_rooms()

    def list_available_rooms(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get list of available and occupied rooms.

        Returns:
            {
                'available': [room_dict, ...],
                'occupied': {room_name: end_time, ...}
            }
        """
        if current_time is None:
            current_time = datetime.now()

        current_time_str = current_time.isoformat()
        rooms = self.repo.get_all_rooms()

        available = []
        occupied = {}

        for room in rooms:
            bookings = self.repo.get_room_bookings(room['name'])

            # Find current booking
            current_booking = None
            for booking in bookings:
                if booking['start_time'] <= current_time_str < booking['end_time']:
                    current_booking = booking
                    break

            if current_booking:
                # Extract end time for display (HH:MM)
                end_dt = datetime.fromisoformat(current_booking['end_time'])
                occupied[room['name']] = end_dt.strftime('%H:%M')
            else:
                available.append(room)

        return {
            'available': available,
            'occupied': occupied
        }

    def book_room(
        self,
        room_name: str,
        user_id: int,
        username: str,
        time_range: str
    ) -> Dict[str, Any]:
        """Book a room for given time range.

        Args:
            room_name: Name of the room to book
            user_id: ID of the user booking
            username: Name of the user booking
            time_range: Time range in format "HH:MM-HH:MM"

        Returns:
            {
                'success': bool,
                'message': str,
                'booking_id': Optional[int]
            }
        """
        # Check if room exists
        room = self.repo.get_room(room_name)
        if not room:
            return {
                'success': False,
                'message': f"❌ Переговорка '{room_name}' не найдена",
                'booking_id': None
            }

        # Parse time range
        try:
            start_time, end_time = self._parse_time_range(time_range)
        except ValueError as e:
            return {
                'success': False,
                'message': f"❌ {str(e)}",
                'booking_id': None
            }

        # Check for conflicts
        conflict = self.repo.check_booking_conflict(
            room_name,
            start_time.isoformat(),
            end_time.isoformat()
        )

        if conflict:
            conflict_start = datetime.fromisoformat(conflict['start_time'])
            conflict_end = datetime.fromisoformat(conflict['end_time'])
            return {
                'success': False,
                'message': (
                    f"❌ {room_name} занят с {conflict_start.strftime('%H:%M')} "
                    f"до {conflict_end.strftime('%H:%M')}"
                ),
                'booking_id': None
            }

        # Create booking
        booking_id = self.repo.create_booking(
            room_name=room_name,
            user_id=user_id,
            username=username,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )

        return {
            'success': True,
            'message': f"✅ {room_name} забронирован на {time_range}",
            'booking_id': booking_id
        }

    def release_room(
        self,
        room_name: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Release a room booking early.

        Args:
            room_name: Name of the room to release
            user_id: ID of the user releasing (must be owner)

        Returns:
            {
                'success': bool,
                'message': str
            }
        """
        # Check if room exists
        room = self.repo.get_room(room_name)
        if not room:
            return {
                'success': False,
                'message': f"❌ Переговорка '{room_name}' не найдена"
            }

        # Find user's booking for this room
        booking = self.repo.find_booking_by_room_and_user(room_name, user_id)

        if not booking:
            return {
                'success': False,
                'message': f"❌ {room_name} забронирован не вами"
            }

        # Delete booking
        success = self.repo.delete_booking(booking['id'])

        if success:
            return {
                'success': True,
                'message': f"✅ {room_name} освобожден"
            }
        else:
            return {
                'success': False,
                'message': f"❌ Не удалось освободить {room_name}"
            }

    def get_room_status(
        self,
        room_name: str,
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get current status of a room.

        Args:
            room_name: Name of the room to check
            current_time: Time to check at (default: now)

        Returns:
            {
                'success': bool,
                'message': str,
                'is_occupied': bool,
                'booking': Optional[Dict]
            }
        """
        if current_time is None:
            current_time = datetime.now()

        # Check if room exists
        room = self.repo.get_room(room_name)
        if not room:
            return {
                'success': False,
                'message': f"❌ Переговорка '{room_name}' не найдена",
                'is_occupied': False,
                'booking': None
            }

        # Find current booking
        current_time_str = current_time.isoformat()
        bookings = self.repo.get_room_bookings(room_name)

        current_booking = None
        for booking in bookings:
            if booking['start_time'] <= current_time_str < booking['end_time']:
                current_booking = booking
                break

        if current_booking:
            end_dt = datetime.fromisoformat(current_booking['end_time'])
            end_time_str = end_dt.strftime('%H:%M')
            return {
                'success': True,
                'message': f"{room_name}: {current_booking['username']}, до {end_time_str}",
                'is_occupied': True,
                'booking': current_booking
            }
        else:
            return {
                'success': True,
                'message': f"{room_name} свободен",
                'is_occupied': False,
                'booking': None
            }

    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a user."""
        return self.repo.get_user_bookings(user_id)
