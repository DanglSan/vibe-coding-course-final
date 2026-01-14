"""Database module for room booking system."""
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager


class Database:
    """SQLite database for room bookings."""

    def __init__(self, db_path: str = "bookings.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Rooms table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    capacity INTEGER NOT NULL
                )
            """)

            # Bookings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (room_name) REFERENCES rooms (name)
                )
            """)

            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bookings_room_time
                ON bookings (room_name, start_time, end_time)
            """)

    # ========================================================================
    # Rooms operations
    # ========================================================================

    def add_room(self, name: str, capacity: int) -> int:
        """Add a new room."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO rooms (name, capacity) VALUES (?, ?)",
                (name, capacity)
            )
            return cursor.lastrowid

    def get_room(self, name: str) -> Optional[Dict[str, Any]]:
        """Get room by name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM rooms WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Get all rooms."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rooms ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def clear_rooms(self):
        """Clear all rooms (for testing)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rooms")

    # ========================================================================
    # Bookings operations
    # ========================================================================

    def create_booking(
        self,
        room_name: str,
        user_id: int,
        username: str,
        start_time: str,
        end_time: str
    ) -> int:
        """Create a new booking."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO bookings
                   (room_name, user_id, username, start_time, end_time, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (room_name, user_id, username, start_time, end_time,
                 datetime.now().isoformat())
            )
            return cursor.lastrowid

    def get_booking(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Get booking by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM bookings WHERE id = ?",
                (booking_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_room_bookings(self, room_name: str) -> List[Dict[str, Any]]:
        """Get all bookings for a room."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM bookings
                   WHERE room_name = ?
                   ORDER BY start_time""",
                (room_name,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM bookings
                   WHERE user_id = ?
                   ORDER BY start_time""",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_booking(self, booking_id: int) -> bool:
        """Delete a booking by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            return cursor.rowcount > 0

    def delete_room_bookings(self, room_name: str) -> int:
        """Delete all bookings for a room. Returns number of deleted bookings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookings WHERE room_name = ?", (room_name,))
            return cursor.rowcount

    def clear_bookings(self):
        """Clear all bookings (for testing)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookings")

    def find_booking_by_room_and_user(
        self,
        room_name: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Find active booking for a room by specific user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM bookings
                   WHERE room_name = ? AND user_id = ?
                   ORDER BY start_time DESC
                   LIMIT 1""",
                (room_name, user_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def check_booking_conflict(
        self,
        room_name: str,
        start_time: str,
        end_time: str
    ) -> Optional[Dict[str, Any]]:
        """Check if there's a booking conflict for given time range.

        Returns conflicting booking if found, None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check for any overlapping bookings
            # Overlap happens when:
            # - new booking starts during existing booking
            # - new booking ends during existing booking
            # - new booking completely contains existing booking
            cursor.execute(
                """SELECT * FROM bookings
                   WHERE room_name = ?
                   AND (
                       (start_time < ? AND end_time > ?)
                       OR (start_time >= ? AND start_time < ?)
                       OR (end_time > ? AND end_time <= ?)
                   )
                   LIMIT 1""",
                (room_name, end_time, start_time,  # contains check
                 start_time, end_time,              # starts during check
                 start_time, end_time)              # ends during check
            )
            row = cursor.fetchone()
            return dict(row) if row else None
