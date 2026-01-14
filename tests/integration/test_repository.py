"""Integration tests for SQLiteRepository (real database operations)."""
import pytest
import tempfile
import os
from src.repository import SQLiteRepository
from datetime import datetime


@pytest.fixture
def sqlite_repo():
    """Create SQLiteRepository with temporary database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    repo = SQLiteRepository(path)
    yield repo
    os.unlink(path)


class TestRoomPersistence:
    """Test that rooms are persisted correctly in SQLite."""

    def test_add_and_retrieve_room(self, sqlite_repo):
        """Test adding and retrieving a room from SQLite."""
        sqlite_repo.add_room("Mars", 6)
        rooms = sqlite_repo.get_all_rooms()
        assert len(rooms) == 1
        assert rooms[0]['name'] == "Mars"
        assert rooms[0]['capacity'] == 6

    def test_multiple_rooms_persistence(self, sqlite_repo):
        """Test adding multiple rooms and retrieving them."""
        sqlite_repo.add_room("Mars", 6)
        sqlite_repo.add_room("Venus", 4)
        sqlite_repo.add_room("Jupiter", 8)

        rooms = sqlite_repo.get_all_rooms()
        assert len(rooms) == 3
        room_names = [r['name'] for r in rooms]
        assert "Mars" in room_names
        assert "Venus" in room_names
        assert "Jupiter" in room_names

    def test_room_retrieval_by_name(self, sqlite_repo):
        """Test retrieving specific room by name."""
        sqlite_repo.add_room("Mars", 6)
        sqlite_repo.add_room("Venus", 4)

        room = sqlite_repo.get_room("Mars")
        assert room is not None
        assert room['name'] == "Mars"
        assert room['capacity'] == 6


class TestBookingPersistence:
    """Test that bookings are persisted correctly in SQLite."""

    def test_create_and_retrieve_booking(self, sqlite_repo):
        """Test creating and retrieving a booking."""
        sqlite_repo.add_room("Mars", 6)
        booking_id = sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="TestUser",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        booking = sqlite_repo.get_booking(booking_id)
        assert booking is not None
        assert booking['username'] == "TestUser"
        assert booking['room_name'] == "Mars"
        assert booking['user_id'] == 12345

    def test_multiple_bookings_for_room(self, sqlite_repo):
        """Test creating multiple bookings for same room."""
        sqlite_repo.add_room("Mars", 6)

        booking_id1 = sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )
        booking_id2 = sqlite_repo.create_booking(
            room_name="Mars",
            user_id=67890,
            username="User2",
            start_time="2026-01-14T17:00:00",
            end_time="2026-01-14T18:00:00"
        )

        bookings = sqlite_repo.get_room_bookings("Mars")
        assert len(bookings) == 2
        assert booking_id1 != booking_id2

    def test_booking_deletion_persistence(self, sqlite_repo):
        """Test that deleted bookings are removed from database."""
        sqlite_repo.add_room("Mars", 6)
        booking_id = sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        # Delete booking
        result = sqlite_repo.delete_booking(booking_id)
        assert result is True

        # Verify it's gone
        booking = sqlite_repo.get_booking(booking_id)
        assert booking is None


class TestConflictDetection:
    """Test booking conflict detection with real database."""

    def test_concurrent_bookings_conflict(self, sqlite_repo):
        """Test that overlapping bookings are detected."""
        sqlite_repo.add_room("Mars", 6)

        # First booking
        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        # Check for conflict with overlapping time
        conflict = sqlite_repo.check_booking_conflict(
            "Mars",
            "2026-01-14T15:30:00",
            "2026-01-14T16:30:00"
        )
        assert conflict is not None
        assert conflict['username'] == "User1"

    def test_no_conflict_different_times(self, sqlite_repo):
        """Test no conflict when bookings don't overlap."""
        sqlite_repo.add_room("Mars", 6)

        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        # Check for non-overlapping time
        conflict = sqlite_repo.check_booking_conflict(
            "Mars",
            "2026-01-14T17:00:00",
            "2026-01-14T18:00:00"
        )
        assert conflict is None

    def test_conflict_exact_time_match(self, sqlite_repo):
        """Test conflict when times match exactly."""
        sqlite_repo.add_room("Mars", 6)

        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        conflict = sqlite_repo.check_booking_conflict(
            "Mars",
            "2026-01-14T15:00:00",
            "2026-01-14T16:00:00"
        )
        assert conflict is not None


class TestUserBookings:
    """Test user-specific booking queries."""

    def test_get_user_bookings(self, sqlite_repo):
        """Test retrieving all bookings for a user."""
        sqlite_repo.add_room("Mars", 6)
        sqlite_repo.add_room("Venus", 4)

        # Create bookings for user 12345
        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )
        sqlite_repo.create_booking(
            room_name="Venus",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T17:00:00",
            end_time="2026-01-14T18:00:00"
        )

        # Create booking for different user
        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=67890,
            username="User2",
            start_time="2026-01-14T19:00:00",
            end_time="2026-01-14T20:00:00"
        )

        bookings = sqlite_repo.get_user_bookings(12345)
        assert len(bookings) == 2
        for booking in bookings:
            assert booking['user_id'] == 12345

    def test_find_booking_by_room_and_user(self, sqlite_repo):
        """Test finding specific user's booking for a room."""
        sqlite_repo.add_room("Mars", 6)

        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        booking = sqlite_repo.find_booking_by_room_and_user("Mars", 12345)
        assert booking is not None
        assert booking['room_name'] == "Mars"
        assert booking['user_id'] == 12345


class TestDataIntegrity:
    """Test data integrity with real SQLite database."""

    def test_room_bookings_relationship(self, sqlite_repo):
        """Test relationship between rooms and bookings."""
        sqlite_repo.add_room("Mars", 6)

        # Create multiple bookings
        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )
        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=67890,
            username="User2",
            start_time="2026-01-14T17:00:00",
            end_time="2026-01-14T18:00:00"
        )

        bookings = sqlite_repo.get_room_bookings("Mars")
        assert len(bookings) == 2

        # Verify all bookings belong to Mars
        for booking in bookings:
            assert booking['room_name'] == "Mars"

    def test_delete_room_bookings(self, sqlite_repo):
        """Test deleting all bookings for a room."""
        sqlite_repo.add_room("Mars", 6)

        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )
        sqlite_repo.create_booking(
            room_name="Mars",
            user_id=67890,
            username="User2",
            start_time="2026-01-14T17:00:00",
            end_time="2026-01-14T18:00:00"
        )

        # Delete all bookings for Mars
        count = sqlite_repo.delete_room_bookings("Mars")
        assert count == 2

        # Verify no bookings remain
        bookings = sqlite_repo.get_room_bookings("Mars")
        assert len(bookings) == 0

    def test_database_persistence_across_operations(self, sqlite_repo):
        """Test that data persists across multiple operations."""
        # Add room
        sqlite_repo.add_room("Mars", 6)

        # Create booking
        booking_id = sqlite_repo.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        # Retrieve and verify room still exists
        room = sqlite_repo.get_room("Mars")
        assert room is not None

        # Retrieve and verify booking still exists
        booking = sqlite_repo.get_booking(booking_id)
        assert booking is not None

        # Delete booking
        sqlite_repo.delete_booking(booking_id)

        # Verify room still exists after booking deleted
        room = sqlite_repo.get_room("Mars")
        assert room is not None
