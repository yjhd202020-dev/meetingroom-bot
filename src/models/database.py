"""
Database models and initialization for meeting room reservations.
Supports both SQLite (local) and PostgreSQL (production).
"""
import os
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Generator, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """Database handler for meeting room reservations."""

    def __init__(self, db_path: str = "./data/meetingroom.db"):
        self.database_url = os.environ.get("DATABASE_URL")
        self.db_path = db_path
        self.is_postgres = bool(self.database_url)

        if self.is_postgres:
            import psycopg2
            self.psycopg2 = psycopg2
            logger.info("📦 Using PostgreSQL database")
            print("📦 Using PostgreSQL database")
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"📦 Using SQLite database: {db_path}")
            print(f"📦 Using SQLite database: {db_path}")

        self.init_db()

    def get_connection(self) -> Any:
        """Get database connection."""
        if self.is_postgres:
            return self.psycopg2.connect(self.database_url)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    @contextmanager
    def get_cursor(self) -> Generator:
        """Context manager for database cursor. Handles connection cleanup automatically."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

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
        with self.get_cursor() as cursor:
            p = self._param()
            cursor.execute(f"SELECT * FROM rooms WHERE LOWER(name) = LOWER({p})", (room_name,))
            row = cursor.fetchone()
            return self._fetchone_dict(cursor, row)

    def check_overlap(self, room_id: int, start_time: datetime, end_time: datetime) -> Optional[Dict]:
        """Check if there's an overlapping reservation."""
        with self.get_cursor() as cursor:
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
            return self._fetchone_dict(cursor, row)

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

        try:
            with self.get_cursor() as cursor:
                p = self._param()
                if self.is_postgres:
                    cursor.execute(f"""
                        INSERT INTO reservations
                        (room_id, slack_user_id, slack_username, start_time, end_time)
                        VALUES ({p}, {p}, {p}, {p}, {p})
                        RETURNING id
                    """, (room_id, slack_user_id, slack_username, start_time, end_time))
                    return cursor.fetchone()[0]
                else:
                    cursor.execute(f"""
                        INSERT INTO reservations
                        (room_id, slack_user_id, slack_username, start_time, end_time)
                        VALUES ({p}, {p}, {p}, {p}, {p})
                    """, (room_id, slack_user_id, slack_username, start_time, end_time))
                    return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            return None

    def get_weekly_reservations(self, start_date: datetime) -> List[Dict]:
        """Get all reservations for the week starting from start_date."""
        from datetime import timedelta
        end_date = start_date + timedelta(days=7)

        with self.get_cursor() as cursor:
            p = self._param()
            cursor.execute(f"""
                SELECT r.*, rm.name as room_name
                FROM reservations r
                JOIN rooms rm ON r.room_id = rm.id
                WHERE r.start_time >= {p} AND r.start_time < {p}
                ORDER BY rm.name, r.start_time
            """, (start_date, end_date))
            return self._fetchall_dict(cursor, cursor.fetchall())

    def get_all_rooms(self) -> List[Dict]:
        """Get all available rooms."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM rooms ORDER BY name")
            return self._fetchall_dict(cursor, cursor.fetchall())

    def get_user_reservations(self, slack_user_id: str) -> List[Dict]:
        """Get all future reservations for a specific user."""
        with self.get_cursor() as cursor:
            now = datetime.now()
            p = self._param()
            cursor.execute(f"""
                SELECT r.*, rm.name as room_name
                FROM reservations r
                JOIN rooms rm ON r.room_id = rm.id
                WHERE r.slack_user_id = {p} AND r.end_time > {p}
                ORDER BY r.start_time
            """, (slack_user_id, now))
            return self._fetchall_dict(cursor, cursor.fetchall())

    def delete_reservation(self, reservation_id: int, slack_user_id: str) -> bool:
        """Delete a reservation by ID. Only allows deletion by the owner."""
        try:
            with self.get_cursor() as cursor:
                p = self._param()
                cursor.execute(f"""
                    DELETE FROM reservations
                    WHERE id = {p} AND slack_user_id = {p}
                """, (reservation_id, slack_user_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting reservation: {e}")
            return False

    def get_reservation_by_id(self, reservation_id: int) -> Optional[Dict]:
        """Get a reservation by ID."""
        with self.get_cursor() as cursor:
            p = self._param()
            cursor.execute(f"""
                SELECT r.*, rm.name as room_name
                FROM reservations r
                JOIN rooms rm ON r.room_id = rm.id
                WHERE r.id = {p}
            """, (reservation_id,))
            return self._fetchone_dict(cursor, cursor.fetchone())

    def get_all_future_reservations(self, limit: int = 50) -> List[Dict]:
        """Get all future reservations across all rooms."""
        with self.get_cursor() as cursor:
            now = datetime.now()
            p = self._param()
            cursor.execute(f"""
                SELECT r.*, rm.name as room_name
                FROM reservations r
                JOIN rooms rm ON r.room_id = rm.id
                WHERE r.end_time > {p}
                ORDER BY r.start_time
                LIMIT {limit}
            """, (now,))
            return self._fetchall_dict(cursor, cursor.fetchall())

    def create_recurring_reservations(
        self,
        room_id: int,
        slack_user_id: str,
        slack_username: str,
        start_hour: int,
        start_minute: int,
        end_hour: int,
        end_minute: int,
        weekday: int,
        weeks: int = 4
    ) -> Tuple[List[int], List[str]]:
        """
        Create recurring reservations for N weeks.

        Args:
            weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
            weeks: Number of weeks to create reservations for

        Returns:
            Tuple of (created_reservation_ids, conflict_dates)
        """
        from datetime import timedelta

        now = datetime.now()
        days_ahead = weekday - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        next_date = now + timedelta(days=days_ahead)
        created_ids: List[int] = []
        conflicts: List[str] = []

        for week in range(weeks):
            target_date = next_date + timedelta(weeks=week)
            start_time = target_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            end_time = target_date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

            # Check for conflict
            conflict = self.check_overlap(room_id, start_time, end_time)
            if conflict:
                conflicts.append(target_date.strftime("%Y-%m-%d"))
                continue

            # Create reservation
            try:
                with self.get_cursor() as cursor:
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
                    created_ids.append(reservation_id)
            except Exception as e:
                logger.error(f"Error creating recurring reservation for {target_date}: {e}")

        return created_ids, conflicts
