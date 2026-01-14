"""Pytest configuration for BDD tests."""
import pytest
from datetime import datetime
from src.repository import InMemoryRepository
from src.service import RoomBookingService


@pytest.fixture
def test_context():
    """Test context to share data between steps."""
    # Create in-memory repository for testing
    repo = InMemoryRepository()
    service = RoomBookingService(repo)

    context = {
        'repository': repo,
        'service': service,
        'rooms': {},
        'bookings': [],
        'current_user': None,
        'current_user_id': 12345,  # Фиксированный ID для тестов
        'current_time': datetime.now(),
        'bot_response': None,
        'available_rooms': [],
        'occupied_rooms': {},
        'booking_created': False,
        'booking_deleted': False,
        'last_booking_id': None,
    }

    return context
