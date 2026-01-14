"""Pytest configuration for BDD tests."""
import pytest
from datetime import datetime


@pytest.fixture
def test_context():
    """Test context to share data between steps."""
    return {
        'rooms': {},
        'bookings': [],
        'current_user': None,
        'current_time': datetime.now(),
        'bot_response': None,
        'available_rooms': [],
        'booking_created': False,
        'booking_deleted': False,
    }
