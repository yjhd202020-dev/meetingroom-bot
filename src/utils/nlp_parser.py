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

=== YOUR TASK ===
Understand the user's natural language request and determine their intent.

INTENT TYPES:
1. "reserve" - User wants to book a meeting room for a specific date/time
2. "recurring" - User wants to create RECURRING/REPEATED reservations (매주, every week, 정기 예약)
3. "cancel" - User wants to cancel an existing reservation
4. "status" - User wants to see reservation schedule for a specific week (이번주/다음주 예약 현황)
5. "all_reservations" - User wants to see ALL future reservations (전체 예약, 모든 예약)
6. "my_reservations" - User wants to see their own reservations only
7. "help" - User wants to see help/guide/wizard (도움말, 헬프, help, wizard, 사용법, 뭐할수있어, 기능)
8. "unknown" - Cannot understand what user wants

=== TIME UNDERSTANDING ===
Korean time expressions:
- 오전 = morning/AM, 오후 = afternoon/PM
- When user says "오후 6시~8시", both 6 and 8 are PM (18:00~20:00)
- "10시~2시" typically means 10:00 AM to 2:00 PM (crossing noon)

=== RECURRING RESERVATION ===
If user says "매주 금요일 16시~18시 뭄바이" or "every Friday 4pm-6pm Mumbai":
- intent = "recurring"
- Extract weekday (0=Monday ... 6=Sunday)
- Extract time

=== CANCEL REQUESTS ===
If user mentions a specific number with cancel intent, extract it as reservation_id.
If no number mentioned, set reservation_id to null.

Return JSON only:
{{
    "intent": "reserve|recurring|cancel|status|all_reservations|my_reservations|help|unknown",
    "room_name": "Delhi|Mumbai|Chennai|null",
    "date": "YYYY-MM-DD or null (for single reservation)",
    "start_hour": 0-23 or null,
    "start_minute": 0-59 or null,
    "end_hour": 0-23 or null,
    "end_minute": 0-59 or null,
    "reservation_id": number or null,
    "week_offset": 0 or 1 or -1,
    "recurring_weekday": 0-6 or null (0=Monday, 4=Friday, 6=Sunday),
    "recurring_weeks": number or 4 (default 4 weeks)
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
                'start_hour': result.get('start_hour'),
                'start_minute': result.get('start_minute', 0),
                'end_hour': result.get('end_hour'),
                'end_minute': result.get('end_minute', 0),
                'reservation_id': result.get('reservation_id'),
                'week_offset': result.get('week_offset', 0),
                'recurring_weekday': result.get('recurring_weekday'),
                'recurring_weeks': result.get('recurring_weeks', 4)
            }

            # Parse datetime for single reservation
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
            return {
                'intent': 'unknown',
                'room_name': None,
                'start_time': None,
                'end_time': None,
                'reservation_id': None,
                'week_offset': 0,
                'recurring_weekday': None,
                'recurring_weeks': 4
            }
