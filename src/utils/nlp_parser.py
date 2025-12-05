"""
Natural language parser for meeting room reservation requests.
Uses OpenAI API for all intent detection and parsing.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from openai import OpenAI


class IntentParser:
    """Parse all user intents using OpenAI."""

    ROOM_NAMES = ["Delhi", "Mumbai", "Chennai"]

    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def parse(self, text: str) -> dict:
        """
        Parse user intent and extract all relevant information using OpenAI.

        Returns:
            {
                'intent': 'reserve' | 'cancel' | 'status' | 'my_reservations' | 'unknown',
                'room_name': str | None,
                'start_time': datetime | None,
                'end_time': datetime | None,
                'reservation_id': int | None,
                'week_offset': int (0=this week, 1=next week, -1=last week)
            }
        """
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        current_weekday = ['월', '화', '수', '목', '금', '토', '일'][now.weekday()]

        # Calculate next Monday for reference
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = (now + timedelta(days=days_until_monday)).strftime("%Y-%m-%d")

        system_prompt = f"""You are a meeting room reservation assistant. Analyze user messages and extract intent and details.

Current date/time: {today} ({current_weekday}) {current_time}
Next Monday: {next_monday}
Available rooms: Delhi, Mumbai, Chennai

INTENT TYPES:
1. "reserve" - User wants to make a reservation
2. "cancel" - User wants to cancel a reservation
3. "status" - User wants to see reservation status (전체 예약, 예약 현황, 이번주/다음주 예약 등)
4. "my_reservations" - User wants to see their own reservations (내 예약, 나의 예약)
5. "unknown" - Cannot determine intent

TIME PARSING RULES:
- "오전" = AM, "오후" = PM
- "오후 6시~8시" = 18:00~20:00 (BOTH times are PM)
- "내일" = tomorrow, "모레" = day after tomorrow
- "다음주 화요일" = next week Tuesday
- "다음주" in status request = week_offset: 1
- "이번주" or no week mention = week_offset: 0
- "지난주" = week_offset: -1

CANCEL PARSING:
- "5번 취소", "5 취소", "#5 취소" → reservation_id: 5
- Just "취소" without number → reservation_id: null (will show list)

Return JSON only:
{{
    "intent": "reserve|cancel|status|my_reservations|unknown",
    "room_name": "Delhi|Mumbai|Chennai|null",
    "date": "YYYY-MM-DD or null",
    "start_hour": 0-23 or null,
    "start_minute": 0-59 or null,
    "end_hour": 0-23 or null,
    "end_minute": 0-59 or null,
    "reservation_id": number or null,
    "week_offset": 0 or 1 or -1
}}

Examples:
- "오후 6시~8시 Mumbai 예약" → {{"intent": "reserve", "room_name": "Mumbai", "date": "{today}", "start_hour": 18, "start_minute": 0, "end_hour": 20, "end_minute": 0, "reservation_id": null, "week_offset": 0}}
- "다음주 화요일 오전 10시~오후 2시 뭄바이" → {{"intent": "reserve", "room_name": "Mumbai", "date": "(next Tuesday)", "start_hour": 10, "start_minute": 0, "end_hour": 14, "end_minute": 0, "reservation_id": null, "week_offset": 0}}
- "다음주 예약 현황" → {{"intent": "status", "room_name": null, "date": null, "start_hour": null, "start_minute": null, "end_hour": null, "end_minute": null, "reservation_id": null, "week_offset": 1}}
- "5번 취소해줘" → {{"intent": "cancel", "room_name": null, "date": null, "start_hour": null, "start_minute": null, "end_hour": null, "end_minute": null, "reservation_id": 5, "week_offset": 0}}
- "내 예약 보여줘" → {{"intent": "my_reservations", "room_name": null, "date": null, "start_hour": null, "start_minute": null, "end_hour": null, "end_minute": null, "reservation_id": null, "week_offset": 0}}
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

            # Build response
            parsed = {
                'intent': result.get('intent', 'unknown'),
                'room_name': result.get('room_name'),
                'start_time': None,
                'end_time': None,
                'reservation_id': result.get('reservation_id'),
                'week_offset': result.get('week_offset', 0)
            }

            # Parse datetime if reservation intent
            if parsed['intent'] == 'reserve' and result.get('date') and result.get('start_hour') is not None:
                try:
                    date = datetime.strptime(result['date'], "%Y-%m-%d")
                    parsed['start_time'] = date.replace(
                        hour=result['start_hour'],
                        minute=result.get('start_minute', 0),
                        second=0,
                        microsecond=0
                    )
                    parsed['end_time'] = date.replace(
                        hour=result['end_hour'],
                        minute=result.get('end_minute', 0),
                        second=0,
                        microsecond=0
                    )
                except (ValueError, KeyError):
                    parsed['intent'] = 'unknown'

            return parsed

        except Exception as e:
            print(f"OpenAI parsing error: {e}")
            return {'intent': 'unknown', 'room_name': None, 'start_time': None, 'end_time': None, 'reservation_id': None, 'week_offset': 0}
