"""
Natural language parser for meeting room reservation requests.
Extracts room name, date, and time from Korean/English messages.
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


class ReservationParser:
    """Parse natural language reservation requests."""

    # Room name patterns (case-insensitive)
    ROOM_NAMES = ["Delhi", "Mumbai", "Chennai"]
    ROOM_PATTERN = r'\b(' + '|'.join(ROOM_NAMES) + r')\b'

    def __init__(self):
        self.now = datetime.now()

    def parse(self, text: str) -> Optional[dict]:
        """
        Parse reservation request from natural language.

        Returns:
            {
                'room_name': str,
                'start_time': datetime,
                'end_time': datetime
            }
            or None if parsing fails
        """
        # Extract room name
        room_name = self._extract_room(text)
        if not room_name:
            return None

        # Extract date
        date = self._extract_date(text)

        # Extract time range
        time_range = self._extract_time_range(text)
        if not time_range:
            return None

        start_hour, start_minute, end_hour, end_minute = time_range

        # Combine date and time
        start_time = date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end_time = date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

        # Validation
        if start_time >= end_time:
            return None
        if start_time < self.now:
            return None

        return {
            'room_name': room_name,
            'start_time': start_time,
            'end_time': end_time
        }

    def _extract_room(self, text: str) -> Optional[str]:
        """Extract room name from text."""
        match = re.search(self.ROOM_PATTERN, text, re.IGNORECASE)
        if match:
            # Return with proper capitalization
            room = match.group(1)
            for name in self.ROOM_NAMES:
                if name.lower() == room.lower():
                    return name
        return None

    def _extract_date(self, text: str) -> datetime:
        """
        Extract date from text. Defaults to today.

        Patterns:
        - "내일" / "tomorrow" → tomorrow
        - "모레" / "day after tomorrow" → day after tomorrow
        - "12월 5일" / "12/5" / "12-5" → specific date
        - No date → today
        """
        today = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Tomorrow
        if re.search(r'내일|tomorrow', text, re.IGNORECASE):
            return today + timedelta(days=1)

        # Day after tomorrow
        if re.search(r'모레|day after tomorrow', text, re.IGNORECASE):
            return today + timedelta(days=2)

        # Specific date: "12월 5일", "12/5", "12-5"
        date_patterns = [
            r'(\d{1,2})월\s*(\d{1,2})일',  # 12월 5일
            r'(\d{1,2})/(\d{1,2})',         # 12/5
            r'(\d{1,2})-(\d{1,2})',         # 12-5
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                try:
                    # Try this year first
                    result = datetime(self.now.year, month, day)
                    # If date is in the past, assume next year
                    if result < today:
                        result = datetime(self.now.year + 1, month, day)
                    return result
                except ValueError:
                    pass  # Invalid date, continue

        # Default to today
        return today

    def _extract_time_range(self, text: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Extract time range from text.

        Returns: (start_hour, start_minute, end_hour, end_minute)

        Patterns:
        - "오후 4:00~6:00" / "4:00pm-6:00pm"
        - "14시~16시" / "14:00-16:00"
        - "오전 10시부터 12시까지"
        """
        # Pattern 1: "오후 4:00~6:00" or "4:00pm~6:00pm"
        pattern1 = r'(오전|오후|am|pm)?\s*(\d{1,2}):?(\d{2})?\s*(?:~|-|부터|to)\s*(오전|오후|am|pm)?\s*(\d{1,2}):?(\d{2})?'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            am_pm1 = match.group(1) or ''
            start_hour = int(match.group(2))
            start_minute = int(match.group(3) or 0)
            am_pm2 = match.group(4) or am_pm1  # Inherit AM/PM from start time
            end_hour = int(match.group(5))
            end_minute = int(match.group(6) or 0)

            # Convert to 24-hour format
            start_hour = self._to_24hour(start_hour, am_pm1)
            end_hour = self._to_24hour(end_hour, am_pm2)

            return (start_hour, start_minute, end_hour, end_minute)

        # Pattern 2: "14시~16시" or "14-16"
        pattern2 = r'(\d{1,2})시?\s*(?:~|-|부터|to)\s*(\d{1,2})시?'
        match = re.search(pattern2, text)
        if match:
            start_hour = int(match.group(1))
            end_hour = int(match.group(2))
            return (start_hour, 0, end_hour, 0)

        return None

    def _to_24hour(self, hour: int, am_pm: str) -> int:
        """Convert hour to 24-hour format based on AM/PM."""
        am_pm_lower = am_pm.lower()

        if '오후' in am_pm_lower or 'pm' in am_pm_lower:
            if hour != 12:
                hour += 12
        elif '오전' in am_pm_lower or 'am' in am_pm_lower:
            if hour == 12:
                hour = 0

        return hour


def is_status_request(text: str) -> bool:
    """Check if the message is requesting reservation status."""
    status_keywords = [
        '전체 예약',
        '예약 현황',
        '이번주',
        '예약 목록',
        'reservation status',
        'show reservations',
        'list reservations'
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in status_keywords)
