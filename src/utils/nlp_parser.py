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
        """
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        weekday_names = ['월', '화', '수', '목', '금', '토', '일']
        current_weekday = weekday_names[now.weekday()]

        # Calculate key dates
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (now + timedelta(days=2)).strftime("%Y-%m-%d")

        # Calculate this week's dates (Mon-Sun)
        days_since_monday = now.weekday()
        this_monday = now - timedelta(days=days_since_monday)
        this_week_dates = {}
        for i, day in enumerate(weekday_names):
            date = (this_monday + timedelta(days=i)).strftime("%Y-%m-%d")
            this_week_dates[f"이번주 {day}요일"] = date

        # Calculate next week's dates (Mon-Sun)
        next_monday = this_monday + timedelta(weeks=1)
        next_week_dates = {}
        for i, day in enumerate(weekday_names):
            date = (next_monday + timedelta(days=i)).strftime("%Y-%m-%d")
            next_week_dates[f"다음주 {day}요일"] = date

        system_prompt = f"""You are a meeting room reservation assistant. Analyze user messages and extract intent and details.

=== CRITICAL DATE INFORMATION ===
Today: {today} ({current_weekday}요일)
Current time: {current_time}
Tomorrow (내일): {tomorrow}
Day after tomorrow (모레): {day_after}

This week dates:
{chr(10).join(f"- {k}: {v}" for k, v in this_week_dates.items())}

Next week dates:
{chr(10).join(f"- {k}: {v}" for k, v in next_week_dates.items())}

Available rooms: Delhi, Mumbai, Chennai (뭄바이=Mumbai, 델리=Delhi, 첸나이=Chennai)

=== INTENT TYPES ===
1. "reserve" - User wants to make a reservation (예약, 잡아줘, 예약해줘)
2. "cancel" - User wants to cancel a reservation (취소, 삭제, 예약 취소하고 싶어, 취소하고 싶어)
3. "status" - User wants to see all reservation status (전체 예약, 예약 현황, 이번주/다음주 예약)
4. "my_reservations" - User wants to see ONLY their own reservations (내 예약, 나의 예약)
5. "unknown" - Cannot determine intent

IMPORTANT: "취소" keyword = always "cancel" intent, even without reservation number

=== TIME PARSING RULES ===
- "오전" = AM (before 12:00)
- "오후" = PM (12:00 or after)
- "오후 6시~8시" = 18:00~20:00 (BOTH times are PM when only one 오후 is mentioned)
- "10~2시" or "10시~2시" without AM/PM = 10:00~14:00 (assume crossing noon)
- If only one time has AM/PM, apply it contextually

=== CANCEL PARSING ===
- "5번 취소", "5 취소" → reservation_id: 5
- Just "취소" without number → reservation_id: null

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
}}"""

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

            parsed = {
                'intent': result.get('intent', 'unknown'),
                'room_name': result.get('room_name'),
                'start_time': None,
                'end_time': None,
                'reservation_id': result.get('reservation_id'),
                'week_offset': result.get('week_offset', 0)
            }

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
