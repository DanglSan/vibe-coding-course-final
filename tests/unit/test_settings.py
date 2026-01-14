"""Unit tests for Settings operations in Database layer."""
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


class TestSettingsOperations:
    """Test settings CRUD operations."""

    def test_set_and_get_setting(self, temp_db):
        """Test setting and retrieving a configuration value."""
        temp_db.set_setting('timezone_offset', '+3')
        value = temp_db.get_setting('timezone_offset')
        assert value == '+3'

    def test_get_nonexistent_setting_returns_none(self, temp_db):
        """Test getting non-existent setting returns None."""
        value = temp_db.get_setting('nonexistent_key')
        assert value is None

    def test_get_nonexistent_setting_with_default(self, temp_db):
        """Test getting non-existent setting with default value."""
        value = temp_db.get_setting('timezone_offset', '+0')
        assert value == '+0'

    def test_update_existing_setting(self, temp_db):
        """Test updating an existing setting (INSERT OR REPLACE)."""
        temp_db.set_setting('timezone_offset', '+3')
        temp_db.set_setting('timezone_offset', '+5')
        value = temp_db.get_setting('timezone_offset')
        assert value == '+5'

    def test_settings_persistence(self, temp_db):
        """Test that settings persist across operations."""
        # Set multiple settings
        temp_db.set_setting('timezone_offset', '+3')
        temp_db.set_setting('language', 'ru')
        temp_db.set_setting('notifications', 'enabled')

        # Retrieve all
        assert temp_db.get_setting('timezone_offset') == '+3'
        assert temp_db.get_setting('language') == 'ru'
        assert temp_db.get_setting('notifications') == 'enabled'

        # Update one
        temp_db.set_setting('language', 'en')

        # Verify updated value and others unchanged
        assert temp_db.get_setting('timezone_offset') == '+3'
        assert temp_db.get_setting('language') == 'en'
        assert temp_db.get_setting('notifications') == 'enabled'
