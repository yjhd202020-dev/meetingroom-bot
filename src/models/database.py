"""
Database models and initialization for meeting room reservations.
Supports both SQLite (local) and PostgreSQL (production).
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
from urllib.parse import urlparse


class Database:
    """Database handler for meeting room reservations."""

    def __init__(self, db_path: str = "./data/meetingroom.db"):
        self.database_url = os.environ.get("DATABASE_URL")
        self.db_path = db_path
        self.is_postgres = bool(self.database_url)

        if self.is_postgres:
            import psycopg2
            self.psycopg2 = psycopg2
            print(f"📦 Using PostgreSQL database")
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            print(f"📦 Using SQLite database: {db_path}")

        self.init_db()

    def get_connection(self):
        """Get database connection."""
        if self.is_postgres:
            conn = self.psycopg2.connect(self.database_url)
            return conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def init_db(self):
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if self.is_postgres:
            # PostgreSQL schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id SERIAL PRIMARY KEY,
                    room_id INTEGER NOT NULL REFERENCES rooms(id),
                    slack_user_id TEXT NOT NULL,
                    slack_username TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reservations_room_time
                ON reservations(room_id, start_time, end_time)
            """)
        else:
            # SQLite schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT
                )
            """)

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
            if self.is_postgres:
                cursor.execute(
                    "INSERT INTO rooms (name, description) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
                    (room_name, description)
                )
            else:
                cursor.execute(
                    "INSERT OR IGNORE INTO rooms (name, description) VALUES (?, ?)",
                    (room_name, description)
                )

        conn.commit()
        conn.close()

    def _param(self, idx: int = None) -> str:
        """Return parameter placeholder based on database type."""
        return "%s" if self.is_postgres else "?"

    def _fetchone_dict(self, cursor, row) -> Optional[Dict]:
        """Convert row to dict based on database type."""
        if row is None:
            return None
        if self.is_postgres:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return dict(row)

    def _fetchall_dict(self, cursor, rows) -> List[Dict]:
        """Convert rows to list of dicts based on database type."""
        if self.is_postgres:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return [dict(row) for row in rows]

    def get_room_by_name(self, room_name: str) -> Optional[Dict]:
        """Get room by name (case-insensitive)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        p = self._param()
        cursor.execute(f"SELECT * FROM rooms WHERE LOWER(name) = LOWER({p})", (room_name,))
        row = cursor.fetchone()
        result = self._fetchone_dict(cursor, row)
        conn.close()
        return result

    def check_overlap(self, room_id: int, start_time: datetime, end_time: datetime) -> Optional[Dict]:
        """Check if there's an overlapping reservation."""
        conn = self.get_connection()
        cursor = conn.cursor()

        p = self._param()
        cursor.execute(f"""
            SELECT r.*, rm.name as room_name
            FROM reservations r
            JOIN rooms rm ON r.room_id = rm.id
            WHERE r.room_id = {p}
            AND r.start_time < {p}
            AND r.end_time > {p}
            ORDER BY r.start_time
            LIMIT 1
        """, (room_id, end_time, start_time))

        row = cursor.fetchone()
        result = self._fetchone_dict(cursor, row)
        conn.close()
        return result

    def create_reservation(
        self,
        room_id: int,
        slack_user_id: str,
        slack_username: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[int]:
        """Create a new reservation."""
        conflict = self.check_overlap(room_id, start_time, end_time)
        if conflict:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            p = self._param()
            if self.is_postgres:
                cursor.execute(f"""
                    INSERT INTO reservations
                    (room_id, slack_user_id, slack_username, start_time, end_time)
                    VALUES ({p}, {p}, {p}, {p}, {p})
                    RETURNING id
                """, (room_id, slack_user_id, slack_username, start_time, end_time))
                reservation_id = cursor.fetchone()[0]
            else:
                cursor.execute(f"""
                    INSERT INTO reservations
                    (room_id, slack_user_id, slack_username, start_time, end_time)
                    VALUES ({p}, {p}, {p}, {p}, {p})
                """, (room_id, slack_user_id, slack_username, start_time, end_time))
                reservation_id = cursor.lastrowid

            conn.commit()
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

        p = self._param()
        cursor.execute(f"""
            SELECT r.*, rm.name as room_name
            FROM reservations r
            JOIN rooms rm ON r.room_id = rm.id
            WHERE r.start_time >= {p} AND r.start_time < {p}
            ORDER BY rm.name, r.start_time
        """, (start_date, end_date))

        rows = cursor.fetchall()
        result = self._fetchall_dict(cursor, rows)
        conn.close()
        return result

    def get_all_rooms(self) -> List[Dict]:
        """Get all available rooms."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rooms ORDER BY name")
        rows = cursor.fetchall()
        result = self._fetchall_dict(cursor, rows)
        conn.close()
        return result

    def get_user_reservations(self, slack_user_id: str) -> List[Dict]:
        """Get all future reservations for a specific user."""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        p = self._param()
        cursor.execute(f"""
            SELECT r.*, rm.name as room_name
            FROM reservations r
            JOIN rooms rm ON r.room_id = rm.id
            WHERE r.slack_user_id = {p} AND r.end_time > {p}
            ORDER BY r.start_time
        """, (slack_user_id, now))

        rows = cursor.fetchall()
        result = self._fetchall_dict(cursor, rows)
        conn.close()
        return result

    def delete_reservation(self, reservation_id: int, slack_user_id: str) -> bool:
        """Delete a reservation by ID. Only allows deletion by the owner."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            p = self._param()
            cursor.execute(f"""
                DELETE FROM reservations
                WHERE id = {p} AND slack_user_id = {p}
            """, (reservation_id, slack_user_id))

            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted
        except Exception as e:
            conn.close()
            print(f"Error deleting reservation: {e}")
            return False

    def get_reservation_by_id(self, reservation_id: int) -> Optional[Dict]:
        """Get a reservation by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        p = self._param()
        cursor.execute(f"""
            SELECT r.*, rm.name as room_name
            FROM reservations r
            JOIN rooms rm ON r.room_id = rm.id
            WHERE r.id = {p}
        """, (reservation_id,))

        row = cursor.fetchone()
        result = self._fetchone_dict(cursor, row)
        conn.close()
        return result
