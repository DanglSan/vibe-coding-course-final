"""Unit tests for Timezone management in Service layer."""
import pytest
from datetime import datetime, timezone, timedelta
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


class TestTimezoneManagement:
    """Test timezone setting and retrieval."""

    def test_set_timezone_positive_offset(self, service):
        """Test setting positive timezone offset."""
        result = service.set_timezone(3)
        assert result['success'] is True
        assert 'UTC+3' in result['message']
        assert '✅' in result['message']

        # Verify setting persisted
        tz_info = service.get_current_timezone()
        assert tz_info['offset'] == '+3'
        assert tz_info['display'] == 'UTC+3'

    def test_set_timezone_negative_offset(self, service):
        """Test setting negative timezone offset."""
        result = service.set_timezone(-5)
        assert result['success'] is True
        assert 'UTC-5' in result['message']

        tz_info = service.get_current_timezone()
        assert tz_info['offset'] == '-5'
        assert tz_info['display'] == 'UTC-5'

    def test_set_timezone_invalid_offset_too_large(self, service):
        """Test setting timezone offset that is too large."""
        result = service.set_timezone(15)
        assert result['success'] is False
        assert '❌' in result['message']
        assert '-12 до +14' in result['message']

    def test_set_timezone_invalid_offset_too_small(self, service):
        """Test setting timezone offset that is too small."""
        result = service.set_timezone(-13)
        assert result['success'] is False
        assert '❌' in result['message']

    def test_get_current_timezone_default(self, service):
        """Test getting default timezone (UTC+0)."""
        tz_info = service.get_current_timezone()
        assert tz_info['offset'] == '+0'
        assert tz_info['display'] == 'UTC+0'

    def test_get_current_timezone_after_set(self, service):
        """Test getting timezone after setting it."""
        service.set_timezone(5)
        tz_info = service.get_current_timezone()
        assert tz_info['offset'] == '+5'
        assert tz_info['display'] == 'UTC+5'


class TestTimezoneAwareDatetime:
    """Test that datetime operations respect configured timezone."""

    def test_now_returns_timezone_aware(self, service):
        """Test that now() returns timezone-aware datetime."""
        current = service.now()
        assert current.tzinfo is not None
        assert isinstance(current.tzinfo, timezone)

    def test_now_respects_configured_timezone(self, service):
        """Test that now() uses configured timezone offset."""
        # Set timezone to UTC+3
        service.set_timezone(3)

        current = service.now()
        expected_offset = timedelta(hours=3)
        assert current.tzinfo.utcoffset(None) == expected_offset

    def test_parse_time_range_with_timezone(self, service):
        """Test that time range parsing creates timezone-aware datetimes."""
        service.set_timezone(3)

        start, end = service._parse_time_range("15:00-16:00")

        # Check timezone aware
        assert start.tzinfo is not None
        assert end.tzinfo is not None

        # Check offset is UTC+3
        expected_offset = timedelta(hours=3)
        assert start.tzinfo.utcoffset(None) == expected_offset
        assert end.tzinfo.utcoffset(None) == expected_offset

        # Check times
        assert start.hour == 15
        assert start.minute == 0
        assert end.hour == 16
        assert end.minute == 0

    def test_booking_uses_configured_timezone(self, service_with_rooms):
        """Test that booking creation uses configured timezone."""
        # Set timezone to UTC+5
        service_with_rooms.set_timezone(5)

        # Book a room
        result = service_with_rooms.book_room("Mars", 12345, "TestUser", "15:00-16:00")
        assert result['success'] is True

        # Retrieve booking and check timezone
        bookings = service_with_rooms.repo.get_room_bookings("Mars")
        assert len(bookings) == 1

        start_time = datetime.fromisoformat(bookings[0]['start_time'])
        # Should be timezone-aware with UTC+5 offset
        assert start_time.tzinfo is not None
        expected_offset = timedelta(hours=5)
        assert start_time.tzinfo.utcoffset(None) == expected_offset

    def test_availability_check_uses_timezone(self, service_with_rooms):
        """Test that availability check respects timezone."""
        # Set timezone to UTC+3
        service_with_rooms.set_timezone(3)

        # Book Mars for 15:00-16:00
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")

        # Check availability at 15:30 (should be occupied)
        tz = timezone(timedelta(hours=3))
        current_time = datetime.now(tz).replace(hour=15, minute=30)

        result = service_with_rooms.list_available_rooms(current_time)

        # Mars should be occupied
        assert "Mars" in result['occupied']
        assert len(result['available']) == 1
        assert result['available'][0]['name'] == "Venus"

    def test_multiple_timezones(self, service_with_rooms):
        """Test changing timezone and verifying operations work correctly."""
        # Start with UTC+3
        service_with_rooms.set_timezone(3)
        tz_info = service_with_rooms.get_current_timezone()
        assert tz_info['offset'] == '+3'

        # Book a room
        result = service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")
        assert result['success'] is True

        # Change to UTC-5
        service_with_rooms.set_timezone(-5)
        tz_info = service_with_rooms.get_current_timezone()
        assert tz_info['offset'] == '-5'

        # Book another room (should use new timezone)
        result = service_with_rooms.book_room("Venus", 67890, "User2", "10:00-11:00")
        assert result['success'] is True

        # Verify both bookings exist
        mars_bookings = service_with_rooms.repo.get_room_bookings("Mars")
        venus_bookings = service_with_rooms.repo.get_room_bookings("Venus")
        assert len(mars_bookings) == 1
        assert len(venus_bookings) == 1
