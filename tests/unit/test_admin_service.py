"""Unit tests for admin functionality in Service layer."""
import pytest
from src.service import RoomBookingService
from src.repository import InMemoryRepository


@pytest.fixture
def service():
    """Service with in-memory repository."""
    repo = InMemoryRepository()
    service = RoomBookingService(repo)
    # Add initial admin
    repo.add_admin(12345, "Admin1")
    return service


@pytest.fixture
def service_with_rooms(service):
    """Service with pre-populated rooms."""
    service.repo.add_room("Mars", 6)
    service.repo.add_room("Venus", 4)
    return service


class TestAdminAuthorization:
    """Test admin authorization checks."""

    def test_is_admin_true(self, service):
        """Test checking admin user."""
        assert service.is_admin(12345) is True

    def test_is_admin_false(self, service):
        """Test checking non-admin user."""
        assert service.is_admin(99999) is False


class TestAddAdmin:
    """Test adding new admins."""

    def test_add_new_admin(self, service):
        """Test adding new admin."""
        result = service.add_admin(67890, "NewAdmin")
        assert result['success'] is True
        assert "✅" in result['message']
        assert "NewAdmin" in result['message']
        assert service.is_admin(67890) is True

    def test_add_existing_admin(self, service):
        """Test adding user who is already admin."""
        result = service.add_admin(12345, "Admin1")
        assert result['success'] is False
        assert "❌" in result['message']
        assert "уже является" in result['message']


class TestRemoveAdmin:
    """Test removing admins."""

    def test_remove_existing_admin(self, service):
        """Test removing existing admin."""
        result = service.remove_admin(12345, "Admin1")
        assert result['success'] is True
        assert "✅" in result['message']
        assert "удален" in result['message']
        assert service.is_admin(12345) is False

    def test_remove_nonexistent_admin(self, service):
        """Test removing user who is not admin."""
        result = service.remove_admin(99999, "NotAdmin")
        assert result['success'] is False
        assert "❌" in result['message']
        assert "не является" in result['message']


class TestListAdmins:
    """Test listing admins."""

    def test_list_admins_single(self, service):
        """Test listing when there's one admin."""
        admins = service.list_admins()
        assert len(admins) == 1
        assert admins[0]['user_id'] == 12345
        assert admins[0]['username'] == "Admin1"

    def test_list_admins_multiple(self, service):
        """Test listing when there are multiple admins."""
        service.add_admin(67890, "Admin2")
        service.add_admin(11111, "Admin3")
        admins = service.list_admins()
        assert len(admins) == 3
        user_ids = [a['user_id'] for a in admins]
        assert 12345 in user_ids
        assert 67890 in user_ids
        assert 11111 in user_ids

    def test_list_admins_after_removal(self, service):
        """Test listing after removing an admin."""
        service.add_admin(67890, "Admin2")
        service.remove_admin(12345, "Admin1")
        admins = service.list_admins()
        assert len(admins) == 1
        assert admins[0]['user_id'] == 67890


class TestAdminAddRoom:
    """Test admin room addition."""

    def test_admin_add_room(self, service):
        """Test admin adding new room."""
        result = service.admin_add_room("Jupiter", 10)
        assert result['success'] is True
        assert "✅" in result['message']
        assert "Jupiter" in result['message']
        assert "10" in result['message']

        rooms = service.list_all_rooms()
        assert len(rooms) == 1
        assert rooms[0]['name'] == "Jupiter"
        assert rooms[0]['capacity'] == 10

    def test_admin_add_duplicate_room(self, service_with_rooms):
        """Test admin adding room that already exists."""
        result = service_with_rooms.admin_add_room("Mars", 8)
        assert result['success'] is False
        assert "❌" in result['message']
        assert "уже существует" in result['message']

    def test_admin_add_multiple_rooms(self, service):
        """Test admin adding multiple rooms."""
        service.admin_add_room("Mars", 6)
        service.admin_add_room("Venus", 4)
        service.admin_add_room("Jupiter", 8)

        rooms = service.list_all_rooms()
        assert len(rooms) == 3
        room_names = [r['name'] for r in rooms]
        assert "Mars" in room_names
        assert "Venus" in room_names
        assert "Jupiter" in room_names


class TestAdminDeleteRoom:
    """Test admin room deletion."""

    def test_admin_delete_room(self, service_with_rooms):
        """Test admin deleting room."""
        result = service_with_rooms.admin_delete_room("Venus")
        assert result['success'] is True
        assert "✅" in result['message']
        assert "Venus" in result['message']
        assert "удалена" in result['message']

    def test_admin_delete_nonexistent_room(self, service_with_rooms):
        """Test admin deleting room that doesn't exist."""
        result = service_with_rooms.admin_delete_room("Nonexistent")
        assert result['success'] is False
        assert "❌" in result['message']
        assert "не найдена" in result['message']

    def test_admin_delete_room_with_bookings(self, service_with_rooms):
        """Test admin deleting room that has bookings."""
        # Create a booking
        service_with_rooms.book_room("Mars", 12345, "User1", "15:00-16:00")

        # Delete the room
        result = service_with_rooms.admin_delete_room("Mars")
        assert result['success'] is True

        # Verify bookings for this room are deleted
        bookings = service_with_rooms.repo.get_room_bookings("Mars")
        assert len(bookings) == 0
