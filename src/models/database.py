"""
Database models and initialization for meeting room reservations.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path


class Database:
    """SQLite database handler for meeting room reservations."""

    def __init__(self, db_path: str = "./data/meetingroom.db"):
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def init_db(self):
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create rooms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        """)

        # Create reservations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                slack_user_id TEXT NOT NULL,
                slack_username TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reservations_room_time
            ON reservations(room_id, start_time, end_time)
        """)

        # Insert default rooms if not exist
        rooms = [
            ("Delhi", "델리 회의실"),
            ("Mumbai", "뭄바이 회의실"),
            ("Chennai", "첸나이 회의실")
        ]

        for room_name, description in rooms:
            cursor.execute(
                "INSERT OR IGNORE INTO rooms (name, description) VALUES (?, ?)",
                (room_name, description)
            )

        conn.commit()
        conn.close()

    def get_room_by_name(self, room_name: str) -> Optional[Dict]:
        """Get room by name (case-insensitive)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM rooms WHERE LOWER(name) = LOWER(?)",
            (room_name,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def check_overlap(self, room_id: int, start_time: datetime, end_time: datetime) -> Optional[Dict]:
        """
        Check if there's an overlapping reservation.
        Returns the conflicting reservation if found, None otherwise.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check for overlap: (new_start < existing_end) AND (new_end > existing_start)
        cursor.execute("""
            SELECT r.*, rm.name as room_name
            FROM reservations r
            JOIN rooms rm ON r.room_id = rm.id
            WHERE r.room_id = ?
            AND r.start_time < ?
            AND r.end_time > ?
            ORDER BY r.start_time
            LIMIT 1
        """, (room_id, end_time, start_time))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def create_reservation(
        self,
        room_id: int,
        slack_user_id: str,
        slack_username: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[int]:
        """
        Create a new reservation.
        Returns reservation ID if successful, None if there's a conflict.
        """
        # Check for overlapping reservations
        conflict = self.check_overlap(room_id, start_time, end_time)
        if conflict:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO reservations
                (room_id, slack_user_id, slack_username, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            """, (room_id, slack_user_id, slack_username, start_time, end_time))

            conn.commit()
            reservation_id = cursor.lastrowid
            conn.close()
            return reservation_id
        except Exception as e:
            conn.close()
            print(f"Error creating reservation: {e}")
            return None

    def get_weekly_reservations(self, start_date: datetime) -> List[Dict]:
        """Get all reservations for the week starting from start_date."""
        from datetime import timedelta

        end_date = start_date + timedelta(days=7)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.*, rm.name as room_name
            FROM reservations r
            JOIN rooms rm ON r.room_id = rm.id
            WHERE r.start_time >= ? AND r.start_time < ?
            ORDER BY rm.name, r.start_time
        """, (start_date, end_date))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_all_rooms(self) -> List[Dict]:
        """Get all available rooms."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rooms ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
