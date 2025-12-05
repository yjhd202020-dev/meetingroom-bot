"""
Natural language parser for meeting room reservation requests.
Uses OpenAI API for accurate Korean/English natural language understanding.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from openai import OpenAI


class ReservationParser:
    """Parse natural language reservation requests using OpenAI."""

    ROOM_NAMES = ["Delhi", "Mumbai", "Chennai"]

    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.now = datetime.now()

    def parse(self, text: str) -> Optional[dict]:
        """
        Parse reservation request from natural language using OpenAI.

        Returns:
            {
                'room_name': str,
                'start_time': datetime,
                'end_time': datetime
            }
            or None if parsing fails
        """
        today = self.now.strftime("%Y-%m-%d")
        current_time = self.now.strftime("%H:%M")

        system_prompt = f"""You are a meeting room reservation parser. Extract reservation details from Korean or English text.

Available rooms: Delhi, Mumbai, Chennai

Current date and time: {today} {current_time}

IMPORTANT TIME PARSING RULES:
- "오전" means AM (before noon)
- "오후" means PM (afternoon/evening)
- "오후 6시" = 18:00
- "오후 6시~8시" = 18:00~20:00 (both times are PM when 오후 is used once)
- If no AM/PM specified and hour ≤ 6, assume PM for typical work hours
- "내일" = tomorrow
- "모레" = day after tomorrow

Return JSON only:
{{
    "room_name": "Delhi|Mumbai|Chennai or null if not found",
    "date": "YYYY-MM-DD",
    "start_hour": 0-23,
    "start_minute": 0-59,
    "end_hour": 0-23,
    "end_minute": 0-59,
    "error": "error message if parsing fails, null otherwise"
}}

Examples:
- "오후 6시~8시 Mumbai" → {{"room_name": "Mumbai", "date": "{today}", "start_hour": 18, "start_minute": 0, "end_hour": 20, "end_minute": 0, "error": null}}
- "내일 오전 10시~12시 Delhi" → {{"room_name": "Delhi", "date": "(tomorrow's date)", "start_hour": 10, "start_minute": 0, "end_hour": 12, "end_minute": 0, "error": null}}
- "14:00-16:00 Chennai" → {{"room_name": "Chennai", "date": "{today}", "start_hour": 14, "start_minute": 0, "end_hour": 16, "end_minute": 0, "error": null}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Validate and convert to datetime
            if result.get("error") or not result.get("room_name"):
                return None

            room_name = result["room_name"]
            if room_name not in self.ROOM_NAMES:
                return None

            # Parse date
            date_str = result.get("date", today)
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                date = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Build datetime objects
            start_time = date.replace(
                hour=result["start_hour"],
                minute=result["start_minute"],
                second=0,
                microsecond=0
            )
            end_time = date.replace(
                hour=result["end_hour"],
                minute=result["end_minute"],
                second=0,
                microsecond=0
            )

            # Validation
            if start_time >= end_time:
                return None

            return {
                'room_name': room_name,
                'start_time': start_time,
                'end_time': end_time
            }

        except Exception as e:
            print(f"OpenAI parsing error: {e}")
            return None


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


def is_cancel_request(text: str) -> bool:
    """Check if the message is requesting to cancel a reservation."""
    cancel_keywords = [
        '취소',
        '삭제',
        '예약 취소',
        '취소해',
        '삭제해',
        'cancel',
        'delete reservation'
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in cancel_keywords)


def is_my_reservations_request(text: str) -> bool:
    """Check if the message is requesting user's own reservations."""
    my_keywords = [
        '내 예약',
        '나의 예약',
        '제 예약',
        'my reservation',
        'my booking'
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in my_keywords)
