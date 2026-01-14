"""Unit tests for Database layer (SQLite operations)."""
import pytest
import tempfile
import os
from src.database import Database


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(path)
    yield db
    os.unlink(path)


class TestRoomOperations:
    """Test room CRUD operations."""

    def test_add_room(self, temp_db):
        """Test adding a new room."""
        temp_db.add_room("Test Room", 10)
        rooms = temp_db.get_all_rooms()
        assert len(rooms) == 1
        assert rooms[0]['name'] == "Test Room"
        assert rooms[0]['capacity'] == 10

    def test_get_room_by_name(self, temp_db):
        """Test retrieving room by name."""
        temp_db.add_room("Mars", 6)
        room = temp_db.get_room("Mars")
        assert room is not None
        assert room['name'] == "Mars"
        assert room['capacity'] == 6

    def test_get_nonexistent_room(self, temp_db):
        """Test retrieving non-existent room returns None."""
        room = temp_db.get_room("Nonexistent")
        assert room is None

    def test_get_all_rooms_empty(self, temp_db):
        """Test getting all rooms when database is empty."""
        rooms = temp_db.get_all_rooms()
        assert rooms == []

    def test_get_all_rooms_multiple(self, temp_db):
        """Test getting all rooms with multiple entries."""
        temp_db.add_room("Mars", 6)
        temp_db.add_room("Venus", 4)
        temp_db.add_room("Jupiter", 8)
        rooms = temp_db.get_all_rooms()
        assert len(rooms) == 3
        room_names = [r['name'] for r in rooms]
        assert "Mars" in room_names
        assert "Venus" in room_names
        assert "Jupiter" in room_names


class TestBookingOperations:
    """Test booking CRUD operations."""

    def test_create_booking(self, temp_db):
        """Test creating a booking."""
        temp_db.add_room("Mars", 6)
        booking_id = temp_db.create_booking(
            room_name="Mars",
            user_id=12345,
            username="Test User",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )
        assert booking_id is not None
        booking = temp_db.get_booking(booking_id)
        assert booking['room_name'] == "Mars"
        assert booking['username'] == "Test User"
        assert booking['user_id'] == 12345

    def test_get_booking_nonexistent(self, temp_db):
        """Test getting non-existent booking returns None."""
        booking = temp_db.get_booking(99999)
        assert booking is None

    def test_get_room_bookings(self, temp_db):
        """Test retrieving all bookings for a room."""
        temp_db.add_room("Mars", 6)
        temp_db.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )
        temp_db.create_booking(
            room_name="Mars",
            user_id=67890,
            username="User2",
            start_time="2026-01-14T17:00:00",
            end_time="2026-01-14T18:00:00"
        )
        bookings = temp_db.get_room_bookings("Mars")
        assert len(bookings) == 2

    def test_get_user_bookings(self, temp_db):
        """Test retrieving all bookings for a user."""
        temp_db.add_room("Mars", 6)
        temp_db.add_room("Venus", 4)

        temp_db.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )
        temp_db.create_booking(
            room_name="Venus",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T17:00:00",
            end_time="2026-01-14T18:00:00"
        )
        temp_db.create_booking(
            room_name="Mars",
            user_id=67890,
            username="User2",
            start_time="2026-01-14T19:00:00",
            end_time="2026-01-14T20:00:00"
        )

        bookings = temp_db.get_user_bookings(12345)
        assert len(bookings) == 2
        for booking in bookings:
            assert booking['user_id'] == 12345

    def test_delete_booking(self, temp_db):
        """Test deleting a booking."""
        temp_db.add_room("Mars", 6)
        booking_id = temp_db.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )
        assert temp_db.delete_booking(booking_id) is True
        booking = temp_db.get_booking(booking_id)
        assert booking is None

    def test_delete_nonexistent_booking(self, temp_db):
        """Test deleting non-existent booking returns False."""
        result = temp_db.delete_booking(99999)
        assert result is False

    def test_check_booking_conflict(self, temp_db):
        """Test checking for booking conflicts."""
        temp_db.add_room("Mars", 6)
        temp_db.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        # Test overlapping booking
        conflict = temp_db.check_booking_conflict(
            "Mars",
            "2026-01-14T15:30:00",
            "2026-01-14T16:30:00"
        )
        assert conflict is not None
        assert conflict['username'] == "User1"

    def test_no_booking_conflict(self, temp_db):
        """Test when there's no booking conflict."""
        temp_db.add_room("Mars", 6)
        temp_db.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        # Test non-overlapping booking
        conflict = temp_db.check_booking_conflict(
            "Mars",
            "2026-01-14T17:00:00",
            "2026-01-14T18:00:00"
        )
        assert conflict is None

    def test_find_booking_by_room_and_user(self, temp_db):
        """Test finding booking by room and user."""
        temp_db.add_room("Mars", 6)
        temp_db.create_booking(
            room_name="Mars",
            user_id=12345,
            username="User1",
            start_time="2026-01-14T15:00:00",
            end_time="2026-01-14T16:00:00"
        )

        booking = temp_db.find_booking_by_room_and_user("Mars", 12345)
        assert booking is not None
        assert booking['room_name'] == "Mars"
        assert booking['user_id'] == 12345

    def test_find_booking_by_room_and_user_not_found(self, temp_db):
        """Test finding booking when user has no booking for room."""
        temp_db.add_room("Mars", 6)
        booking = temp_db.find_booking_by_room_and_user("Mars", 99999)
        assert booking is None


class TestDatabaseSchema:
    """Test database schema initialization."""

    def test_tables_created(self, temp_db):
        """Test that required tables are created."""
        with temp_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'rooms' in tables
            assert 'bookings' in tables

    def test_rooms_table_schema(self, temp_db):
        """Test rooms table has correct schema."""
        with temp_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(rooms)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            assert 'id' in columns
            assert 'name' in columns
            assert 'capacity' in columns

    def test_bookings_table_schema(self, temp_db):
        """Test bookings table has correct schema."""
        with temp_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(bookings)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            assert 'id' in columns
            assert 'room_name' in columns
            assert 'user_id' in columns
            assert 'username' in columns
            assert 'start_time' in columns
            assert 'end_time' in columns
