"""
Natural language parser for meeting room reservation requests.
Uses OpenAI API for conversational understanding.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from openai import OpenAI


class IntentParser:
    """Parse user intents using OpenAI with natural conversation style."""

    ROOM_NAMES = ["Delhi", "Mumbai", "Chennai"]

    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def parse(self, text: str) -> dict:
        """Parse user's natural language request."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][now.weekday()]

        # 날짜 계산
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (now + timedelta(days=2)).strftime("%Y-%m-%d")

        # 이번주/다음주 날짜 계산
        days_since_monday = now.weekday()
        this_monday = now - timedelta(days=days_since_monday)

        week_dates = []
        for i, day in enumerate(['월', '화', '수', '목', '금', '토', '일']):
            this_date = (this_monday + timedelta(days=i)).strftime("%Y-%m-%d")
            next_date = (this_monday + timedelta(days=i+7)).strftime("%Y-%m-%d")
            week_dates.append(f"이번주 {day}요일={this_date}, 다음주 {day}요일={next_date}")

        system_prompt = f"""너는 회의실 예약을 도와주는 친절한 비서야. 사용자의 자연어 메시지를 이해해서 의도를 파악해.

## 현재 시간 정보
- 오늘: {today} ({weekday_kr}요일)
- 현재 시각: {current_time}
- 내일: {tomorrow}
- 모레: {day_after}
- {chr(10).join(week_dates)}

## 회의실
Delhi(델리), Mumbai(뭄바이), Chennai(첸나이) 3개가 있어.

## 의도 분류

1. **help** - 도움말/사용법 요청
   - "help", "도움말", "사용법", "뭐 할 줄 알아?", "기능", "wizard", "뭐해?", "할 줄 아는거", "어떻게 써?"

2. **reserve** - 일회성 예약
   - "오늘 3시~5시 델리 예약", "내일 오후 2시부터 4시까지 뭄바이"
   - 반드시 날짜 + 시간 + 회의실이 있어야 함

3. **recurring** - 반복 예약 (매주)
   - "매주 금요일 16~18 뭄바이", "every friday 4pm mumbai"
   - "매주" 또는 "every week" 키워드가 있으면 recurring

4. **cancel** - 예약 취소
   - "취소", "cancel", "5번 취소", "예약 취소할래"

5. **status** - 특정 주 예약 현황
   - "이번주 예약 현황", "다음주 뭐 있어?", "이번주 스케줄"

6. **all_reservations** - 전체 예약 보기
   - "전체 예약", "모든 예약", "예약 현황 전체"

7. **my_reservations** - 내 예약만 보기
   - "내 예약", "my reservations", "내가 뭐 예약했지?"

8. **unknown** - 위에 해당 안 되는 경우

## 시간 해석
- "오후 4시~6시" = 16:00~18:00 (둘 다 오후)
- "16~18" = 16:00~18:00
- "4시~6시" (오전/오후 안 붙으면) = 문맥상 판단, 보통 업무시간이면 오후
- "오전 10시~오후 2시" = 10:00~14:00

## JSON 응답 형식
{{
  "intent": "help|reserve|recurring|cancel|status|all_reservations|my_reservations|unknown",
  "room_name": "Delhi|Mumbai|Chennai|null",
  "date": "YYYY-MM-DD 또는 null",
  "start_hour": 0-23 또는 null,
  "start_minute": 0-59 또는 null (기본값 0),
  "end_hour": 0-23 또는 null,
  "end_minute": 0-59 또는 null (기본값 0),
  "reservation_id": 숫자 또는 null,
  "week_offset": 0(이번주) 또는 1(다음주) 또는 -1(지난주),
  "recurring_weekday": 0(월)~6(일) 또는 null,
  "recurring_weeks": 반복 주수 (기본값 4)
}}

중요: JSON만 반환해. 다른 텍스트 없이."""

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
            print(f"[NLP] Input: '{text}' -> Parsed: {result}")

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

            # 일회성 예약인 경우 datetime 객체 생성
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
                except (ValueError, KeyError) as e:
                    print(f"[NLP] Date parsing error: {e}")
                    # 시간 정보 부족하면 그대로 둠 (handler에서 처리)

            return parsed

        except Exception as e:
            print(f"[NLP] OpenAI error: {e}")
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
