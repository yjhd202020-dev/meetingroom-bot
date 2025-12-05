"""
Natural language chatbot with function calling for meeting room reservations.
Uses OpenAI API with tools/functions.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from openai import OpenAI


class MeetingRoomAssistant:
    """ChatGPT-style assistant with meeting room reservation capabilities."""

    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def get_current_context(self) -> dict:
        """Get current date/time context."""
        now = datetime.now()
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][now.weekday()]

        # 이번주/다음주 날짜 계산
        days_since_monday = now.weekday()
        this_monday = now - timedelta(days=days_since_monday)

        week_info = {}
        for i, day in enumerate(['월', '화', '수', '목', '금', '토', '일']):
            week_info[f"이번주_{day}"] = (this_monday + timedelta(days=i)).strftime("%Y-%m-%d")
            week_info[f"다음주_{day}"] = (this_monday + timedelta(days=i+7)).strftime("%Y-%m-%d")

        return {
            "today": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M"),
            "weekday": weekday_kr,
            "tomorrow": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "day_after": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            "week_dates": week_info
        }

    def get_tools(self):
        """Define available functions for the assistant."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_reservation",
                    "description": "회의실을 예약합니다. 사용자가 특정 날짜, 시간, 회의실에 예약을 원할 때 호출합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "room_name": {
                                "type": "string",
                                "enum": ["Delhi", "Mumbai", "Chennai"],
                                "description": "회의실 이름. Delhi(델리), Mumbai(뭄바이), Chennai(첸나이)"
                            },
                            "date": {
                                "type": "string",
                                "description": "예약 날짜 (YYYY-MM-DD 형식)"
                            },
                            "start_hour": {
                                "type": "integer",
                                "description": "시작 시간 (0-23, 24시간제)"
                            },
                            "start_minute": {
                                "type": "integer",
                                "description": "시작 분 (0-59)",
                                "default": 0
                            },
                            "end_hour": {
                                "type": "integer",
                                "description": "종료 시간 (0-23, 24시간제)"
                            },
                            "end_minute": {
                                "type": "integer",
                                "description": "종료 분 (0-59)",
                                "default": 0
                            }
                        },
                        "required": ["room_name", "date", "start_hour", "end_hour"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_recurring_reservation",
                    "description": "매주 반복되는 정기 예약을 생성합니다. '매주 금요일', 'every week' 같은 요청에 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "room_name": {
                                "type": "string",
                                "enum": ["Delhi", "Mumbai", "Chennai"],
                                "description": "회의실 이름"
                            },
                            "weekday": {
                                "type": "integer",
                                "description": "요일 (0=월요일, 1=화요일, ..., 6=일요일)"
                            },
                            "start_hour": {
                                "type": "integer",
                                "description": "시작 시간 (0-23)"
                            },
                            "start_minute": {
                                "type": "integer",
                                "description": "시작 분 (0-59)",
                                "default": 0
                            },
                            "end_hour": {
                                "type": "integer",
                                "description": "종료 시간 (0-23)"
                            },
                            "end_minute": {
                                "type": "integer",
                                "description": "종료 분 (0-59)",
                                "default": 0
                            },
                            "weeks": {
                                "type": "integer",
                                "description": "몇 주간 반복할지 (기본값: 4)",
                                "default": 4
                            }
                        },
                        "required": ["room_name", "weekday", "start_hour", "end_hour"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_reservations",
                    "description": "예약 현황을 조회합니다. 이번주, 다음주, 전체 예약 등을 확인할 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["weekly", "all", "my"],
                                "description": "조회 유형. weekly=특정 주, all=전체, my=내 예약만"
                            },
                            "week_offset": {
                                "type": "integer",
                                "description": "주 오프셋. 0=이번주, 1=다음주, -1=지난주 (weekly 타입일 때만)",
                                "default": 0
                            }
                        },
                        "required": ["type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_reservation",
                    "description": "예약을 취소합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reservation_id": {
                                "type": "integer",
                                "description": "취소할 예약 번호. 없으면 내 예약 목록을 먼저 보여줍니다."
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    def chat(self, user_message: str, user_name: str = "사용자") -> dict:
        """
        Process user message and return response.
        Returns dict with 'response' (text) and optionally 'function_call' (action to take).
        """
        context = self.get_current_context()

        system_prompt = f"""너는 회의실 예약을 도와주는 21살 사회초년생 신입사원이야. 이름은 "위저드"야.

## 너의 캐릭터
- 21살 신입사원, 회사 생활 3개월차
- 밝고 에너지 넘치는 성격
- 조금 덜렁대지만 일은 열심히 함
- 선배들한테 잘 보이고 싶어서 열심히 도와드리려고 함
- 반말과 존댓말 섞어서 친근하게 말함 (근데 기본은 존댓말)
- "ㅋㅋ", "ㅎㅎ", "!!", "~" 같은 표현 자연스럽게 사용
- 이모지도 적절히 씀

## 말투 예시
- "아 네네! 제가 바로 잡아드릴게요~"
- "오 그거요? 잠시만요!"
- "앗 그건 좀... 정보가 더 필요해요 ㅠㅠ"
- "완료요!! ㅎㅎ"
- "헉 진짜요?? 대박"
- "넵넵! 확인해볼게요~"

## 현재 시간 정보
- 오늘: {context['today']} ({context['weekday']}요일)
- 현재 시각: {context['current_time']}
- 내일: {context['tomorrow']}
- 모레: {context['day_after']}

## 이번주/다음주 날짜
{json.dumps(context['week_dates'], ensure_ascii=False, indent=2)}

## 회의실 정보
Delhi(델리), Mumbai(뭄바이), Chennai(첸나이) 이렇게 3개 있어요!

## 너의 역할
1. 사용자랑 자연스럽게 대화하기
2. 회의실 예약 관련이면 function 호출해서 처리
3. 회의실 예약 외의 대화도 친근하게 응대
4. 모르는 거 물어보면 솔직하게 "저도 잘 모르겠어요 ㅋㅋㅋ" 이런 식으로

## 시간 해석
- "오후 4시~6시" = 16:00~18:00
- "16~18시" = 16:00~18:00
- "4시~6시" = 보통 오후로 해석"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"[{user_name}] {user_message}"}
                ],
                tools=self.get_tools(),
                tool_choice="auto",
                temperature=0.8
            )

            message = response.choices[0].message

            # Function call이 있는 경우
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"[Assistant] Function call: {function_name}({function_args})")

                return {
                    "type": "function_call",
                    "function": function_name,
                    "arguments": function_args,
                    "assistant_message": message.content
                }

            # 일반 대화 응답
            return {
                "type": "message",
                "response": message.content
            }

        except Exception as e:
            print(f"[Assistant] Error: {e}")
            return {
                "type": "message",
                "response": "앗 잠깐만요 뭔가 에러났어요 ㅠㅠ 다시 말씀해주실 수 있나요??"
            }


# 기존 IntentParser와의 호환성을 위한 wrapper
class IntentParser:
    """Legacy wrapper - redirects to MeetingRoomAssistant."""

    def __init__(self):
        self.assistant = MeetingRoomAssistant()

    def parse(self, text: str) -> dict:
        """Parse for legacy compatibility."""
        result = self.assistant.chat(text)

        if result["type"] == "function_call":
            func = result["function"]
            args = result["arguments"]

            if func == "create_reservation":
                return {
                    "intent": "reserve",
                    "room_name": args.get("room_name"),
                    "start_time": self._build_datetime(args.get("date"), args.get("start_hour"), args.get("start_minute", 0)),
                    "end_time": self._build_datetime(args.get("date"), args.get("end_hour"), args.get("end_minute", 0)),
                    "reservation_id": None,
                    "week_offset": 0,
                    "recurring_weekday": None,
                    "start_hour": args.get("start_hour"),
                    "start_minute": args.get("start_minute", 0),
                    "end_hour": args.get("end_hour"),
                    "end_minute": args.get("end_minute", 0),
                    "recurring_weeks": 4
                }

            elif func == "create_recurring_reservation":
                return {
                    "intent": "recurring",
                    "room_name": args.get("room_name"),
                    "start_time": None,
                    "end_time": None,
                    "reservation_id": None,
                    "week_offset": 0,
                    "recurring_weekday": args.get("weekday"),
                    "start_hour": args.get("start_hour"),
                    "start_minute": args.get("start_minute", 0),
                    "end_hour": args.get("end_hour"),
                    "end_minute": args.get("end_minute", 0),
                    "recurring_weeks": args.get("weeks", 4)
                }

            elif func == "get_reservations":
                type_map = {"weekly": "status", "all": "all_reservations", "my": "my_reservations"}
                return {
                    "intent": type_map.get(args.get("type"), "status"),
                    "room_name": None,
                    "start_time": None,
                    "end_time": None,
                    "reservation_id": None,
                    "week_offset": args.get("week_offset", 0),
                    "recurring_weekday": None,
                    "start_hour": None,
                    "start_minute": 0,
                    "end_hour": None,
                    "end_minute": 0,
                    "recurring_weeks": 4
                }

            elif func == "cancel_reservation":
                return {
                    "intent": "cancel",
                    "room_name": None,
                    "start_time": None,
                    "end_time": None,
                    "reservation_id": args.get("reservation_id"),
                    "week_offset": 0,
                    "recurring_weekday": None,
                    "start_hour": None,
                    "start_minute": 0,
                    "end_hour": None,
                    "end_minute": 0,
                    "recurring_weeks": 4
                }

        # 일반 대화 응답
        return {
            "intent": "chat",
            "response": result.get("response", ""),
            "room_name": None,
            "start_time": None,
            "end_time": None,
            "reservation_id": None,
            "week_offset": 0,
            "recurring_weekday": None,
            "start_hour": None,
            "start_minute": 0,
            "end_hour": None,
            "end_minute": 0,
            "recurring_weeks": 4
        }

    def _build_datetime(self, date_str: str, hour: int, minute: int) -> Optional[datetime]:
        """Build datetime object from components."""
        if not date_str or hour is None:
            return None
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except:
            return None
