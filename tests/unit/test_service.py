"""Unit tests for Service layer (business logic)."""
import pytest
from datetime import datetime
from src.service import RoomBookingService
from src.repository import InMemoryRepository


@pytest.fixture
def service():
    """Create service with in-memory repository."""
    repo = InMemoryRepository()
    return RoomBookingService(repo)


@pytest.fixture
def service_with_rooms(service):
    """Service with pre-populated rooms."""
    service.repo.add_room("Mars", 6)
    service.repo.add_room("Venus", 4)
    return service


class TestListRooms:
    """Test room listing functionality."""

    def test_list_all_rooms_empty(self, service):
        """Test listing rooms when none exist."""
        rooms = service.list_all_rooms()
        assert rooms == []

    def test_list_all_rooms(self, service_with_rooms):
        """Test listing all rooms."""
        rooms = service_with_rooms.list_all_rooms()
        assert len(rooms) == 2
        names = [r['name'] for r in rooms]
        assert "Mars" in names
        assert "Venus" in names


class TestAvailableRooms:
    """Test room availability checking."""

    def test_all_rooms_available(self, service_with_rooms):
        """Test when all rooms are available."""
        current_time = datetime(2026, 1, 14, 15, 0)
        result = service_with_rooms.list_available_rooms(current_time)
        assert len(result['available']) == 2
        assert len(result['occupied']) == 0

    def test_some_rooms_occupied(self, service_with_rooms):
        """Test when some rooms are occupied."""
        # Book Mars
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        current_time = datetime(2026, 1, 14, 15, 30)
        result = service_with_rooms.list_available_rooms(current_time)
        assert len(result['available']) == 1
        assert result['available'][0]['name'] == "Venus"
        assert "Mars" in result['occupied']
        assert result['occupied']['Mars'] == "16:00"

    def test_room_occupied_then_freed(self, service_with_rooms):
        """Test room becomes available after booking ends."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")

        # During booking
        current_time = datetime(2026, 1, 14, 15, 30)
        result = service_with_rooms.list_available_rooms(current_time)
        assert len(result['available']) == 1
        assert "Mars" in result['occupied']

        # After booking
        current_time = datetime(2026, 1, 14, 16, 30)
        result = service_with_rooms.list_available_rooms(current_time)
        assert len(result['available']) == 2
        assert "Mars" not in result['occupied']


class TestBookRoom:
    """Test room booking logic."""

    def test_book_available_room(self, service_with_rooms):
        """Test booking an available room."""
        result = service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        assert result['success'] is True
        assert "✅" in result['message']
        assert "Mars забронирован" in result['message']
        assert result['booking_id'] is not None

    def test_book_occupied_room(self, service_with_rooms):
        """Test booking an already occupied room."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        result = service_with_rooms.book_room("Mars", 67890, "User2", "15:00-16:00")
        assert result['success'] is False
        assert "❌" in result['message']
        assert "занят" in result['message']
        assert result['booking_id'] is None

    def test_book_nonexistent_room(self, service_with_rooms):
        """Test booking a room that doesn't exist."""
        result = service_with_rooms.book_room("Jupiter", 12345, "User1", "15:00-16:00")
        assert result['success'] is False
        assert "не найдена" in result['message']
        assert result['booking_id'] is None

    def test_book_invalid_time_format(self, service_with_rooms):
        """Test booking with invalid time format."""
        result = service_with_rooms.book_room("Mars", 12345, "User1", "invalid")
        assert result['success'] is False
        assert "❌" in result['message']
        assert result['booking_id'] is None

    def test_book_end_before_start(self, service_with_rooms):
        """Test booking where end time is before start time."""
        result = service_with_rooms.book_room("Mars", 12345, "User1", "16:00-15:00")
        assert result['success'] is False
        assert "раньше" in result['message']
        assert result['booking_id'] is None

    def test_book_overlapping_time(self, service_with_rooms):
        """Test booking with overlapping time."""
        service_with_rooms.book_room("Mars", 12345, "User1", "14:00-15:00")
        result = service_with_rooms.book_room("Mars", 67890, "User2", "14:30-15:30")
        assert result['success'] is False
        assert "❌" in result['message']
        assert "занят" in result['message']


class TestReleaseRoom:
    """Test room release logic."""

    def test_release_own_booking(self, service_with_rooms):
        """Test releasing own booking."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        result = service_with_rooms.release_room("Mars", 12345)
        assert result['success'] is True
        assert "✅" in result['message']
        assert "освобожден" in result['message']

    def test_release_others_booking(self, service_with_rooms):
        """Test attempting to release someone else's booking."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        result = service_with_rooms.release_room("Mars", 67890)
        assert result['success'] is False
        assert "не вами" in result['message']

    def test_release_nonexistent_room(self, service_with_rooms):
        """Test releasing a room that doesn't exist."""
        result = service_with_rooms.release_room("Jupiter", 12345)
        assert result['success'] is False
        assert "не найдена" in result['message']

    def test_release_unbooked_room(self, service_with_rooms):
        """Test releasing a room that isn't booked."""
        result = service_with_rooms.release_room("Mars", 12345)
        assert result['success'] is False
        assert "не вами" in result['message']


class TestRoomStatus:
    """Test room status queries."""

    def test_status_free_room(self, service_with_rooms):
        """Test status of free room."""
        current_time = datetime(2026, 1, 14, 15, 0)
        result = service_with_rooms.get_room_status("Mars", current_time)
        assert result['success'] is True
        assert "свободен" in result['message']
        assert result['is_occupied'] is False
        assert result['booking'] is None

    def test_status_occupied_room(self, service_with_rooms):
        """Test status of occupied room."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        current_time = datetime(2026, 1, 14, 15, 30)
        result = service_with_rooms.get_room_status("Mars", current_time)
        assert result['success'] is True
        assert "User1" in result['message']
        assert "16:00" in result['message']
        assert result['is_occupied'] is True
        assert result['booking'] is not None

    def test_status_nonexistent_room(self, service_with_rooms):
        """Test status of room that doesn't exist."""
        current_time = datetime(2026, 1, 14, 15, 0)
        result = service_with_rooms.get_room_status("Jupiter", current_time)
        assert result['success'] is False
        assert "не найдена" in result['message']
        assert result['is_occupied'] is False
        assert result['booking'] is None

    def test_status_with_default_time(self, service_with_rooms):
        """Test status query without specifying time (uses current time)."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        # Without providing current_time, it should use datetime.now()
        result = service_with_rooms.get_room_status("Mars")
        assert result['success'] is True


class TestTimeFormatting:
    """Test time parsing and formatting."""

    def test_parse_time_range_valid(self, service):
        """Test parsing valid time range."""
        start, end = service._parse_time_range("15:00-16:00")
        assert start.hour == 15
        assert start.minute == 0
        assert end.hour == 16
        assert end.minute == 0

    def test_parse_time_range_different_times(self, service):
        """Test parsing different valid time ranges."""
        start, end = service._parse_time_range("09:30-10:45")
        assert start.hour == 9
        assert start.minute == 30
        assert end.hour == 10
        assert end.minute == 45

    def test_parse_time_range_single_digit_hours(self, service):
        """Test parsing with single digit hours."""
        start, end = service._parse_time_range("9:00-10:00")
        assert start.hour == 9
        assert end.hour == 10

    def test_parse_time_range_invalid_format(self, service):
        """Test parsing invalid time format."""
        with pytest.raises(ValueError) as exc_info:
            service._parse_time_range("invalid")
        assert "Неверный формат" in str(exc_info.value)

    def test_parse_time_range_missing_separator(self, service):
        """Test parsing time range without separator."""
        with pytest.raises(ValueError) as exc_info:
            service._parse_time_range("15:00 16:00")
        assert "Неверный формат" in str(exc_info.value)

    def test_parse_time_range_invalid_time_values(self, service):
        """Test parsing with invalid time values."""
        with pytest.raises(ValueError) as exc_info:
            service._parse_time_range("25:00-26:00")
        assert "Неверный формат" in str(exc_info.value)

    def test_parse_time_range_end_before_start(self, service):
        """Test parsing where end time is before start time."""
        with pytest.raises(ValueError) as exc_info:
            service._parse_time_range("16:00-15:00")
        assert "раньше" in str(exc_info.value)

    def test_parse_time_range_equal_times(self, service):
        """Test parsing where start and end times are equal."""
        with pytest.raises(ValueError) as exc_info:
            service._parse_time_range("15:00-15:00")
        assert "раньше" in str(exc_info.value)


class TestUserBookings:
    """Test user booking queries."""

    def test_get_user_bookings_empty(self, service_with_rooms):
        """Test getting bookings when user has none."""
        bookings = service_with_rooms.get_user_bookings(12345)
        assert bookings == []

    def test_get_user_bookings_single(self, service_with_rooms):
        """Test getting single booking for user."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        bookings = service_with_rooms.get_user_bookings(12345)
        assert len(bookings) == 1
        assert bookings[0]['room_name'] == "Mars"
        assert bookings[0]['user_id'] == 12345

    def test_get_user_bookings_multiple(self, service_with_rooms):
        """Test getting multiple bookings for user."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        service_with_rooms.book_room("Venus", 12345, "User1", "17:00-18:00")
        bookings = service_with_rooms.get_user_bookings(12345)
        assert len(bookings) == 2
        room_names = [b['room_name'] for b in bookings]
        assert "Mars" in room_names
        assert "Venus" in room_names

    def test_get_user_bookings_different_users(self, service_with_rooms):
        """Test that user only sees their own bookings."""
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        service_with_rooms.book_room("Venus", 67890, "User2", "17:00-18:00")
        bookings = service_with_rooms.get_user_bookings(12345)
        assert len(bookings) == 1
        assert bookings[0]['room_name'] == "Mars"
