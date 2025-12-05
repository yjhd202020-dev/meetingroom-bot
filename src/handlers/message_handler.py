"""
Slack message event handlers.
"""
from slack_bolt import App
from utils.nlp_parser import IntentParser
from services.reservation_service import ReservationService


def get_help_message() -> str:
    """Return comprehensive help message."""
    return """안녕하세요! 저는 회의실 예약을 도와드리는 봇이에요 🤖

*🏢 사용 가능한 회의실*
Delhi(델리) | Mumbai(뭄바이) | Chennai(첸나이)

*📅 예약하기*
그냥 편하게 말씀하시면 돼요!
• `오늘 오후 3시~5시 델리 예약해줘`
• `내일 10시부터 12시까지 뭄바이`
• `다음주 화요일 14~16시 첸나이`

*🔁 매주 반복 예약*
• `매주 금요일 16~18시 뭄바이`
• `매주 월요일 오전 10시~12시 델리`

*📋 예약 확인*
• `이번주 예약 현황` - 이번주 스케줄
• `전체 예약` - 모든 예약 보기
• `내 예약` - 내가 한 예약만

*❌ 예약 취소*
• `내 예약` 확인 후 → `3번 취소`

편하게 물어보세요! 😊"""


def get_user_display_name(client, user_id: str) -> str:
    """Get user's display name from Slack API."""
    try:
        result = client.users_info(user=user_id)
        if result["ok"]:
            user = result["user"]
            profile = user.get("profile", {})
            display_name = profile.get("display_name") or profile.get("real_name") or user.get("name", "Unknown")
            return display_name
    except Exception as e:
        print(f"Error fetching user info: {e}")
    return "Unknown"


def handle_intent(parsed: dict, user_id: str, user_name: str, reservation_service: ReservationService, say):
    """Handle parsed intent and respond."""
    intent = parsed['intent']

    if intent == 'help':
        say(get_help_message())

    elif intent == 'status':
        status = reservation_service.get_weekly_status(parsed['week_offset'])
        say(status)

    elif intent == 'all_reservations':
        status = reservation_service.get_all_reservations()
        say(status)

    elif intent == 'my_reservations':
        result = reservation_service.get_user_reservations(user_id)
        say(result['message'])

    elif intent == 'cancel':
        if parsed['reservation_id']:
            result = reservation_service.cancel_reservation(parsed['reservation_id'], user_id)
            say(result['message'])
        else:
            # 취소할 예약 번호를 안 알려줬으면 목록 보여주기
            result = reservation_service.get_user_reservations(user_id)
            if result['reservations']:
                say(
                    "어떤 예약을 취소할까요? 🤔\n\n"
                    f"{result['message']}\n\n"
                    "_취소할 예약 번호를 알려주세요! (예: `3번 취소`)_"
                )
            else:
                say("취소할 예약이 없어요! 📭")

    elif intent == 'reserve':
        if parsed['room_name'] and parsed['start_time'] and parsed['end_time']:
            result = reservation_service.create_reservation(
                room_name=parsed['room_name'],
                slack_user_id=user_id,
                slack_username=user_name,
                start_time=parsed['start_time'],
                end_time=parsed['end_time']
            )
            say(result['message'])
        else:
            # 정보 부족 시 친절하게 안내
            missing = []
            if not parsed['room_name']:
                missing.append("회의실 (Delhi/Mumbai/Chennai)")
            if not parsed['start_time']:
                missing.append("날짜와 시간")

            say(
                f"예약하려면 조금 더 정보가 필요해요! 🙏\n\n"
                f"*부족한 정보:* {', '.join(missing)}\n\n"
                "*예시:*\n"
                "• `오늘 오후 3시~5시 델리`\n"
                "• `내일 10~12시 뭄바이`\n"
                "• `다음주 월요일 14~16시 첸나이`"
            )

    elif intent == 'recurring':
        if (parsed['room_name'] and
            parsed['recurring_weekday'] is not None and
            parsed['start_hour'] is not None and
            parsed['end_hour'] is not None):
            result = reservation_service.create_recurring_reservation(
                room_name=parsed['room_name'],
                slack_user_id=user_id,
                slack_username=user_name,
                weekday=parsed['recurring_weekday'],
                start_hour=parsed['start_hour'],
                start_minute=parsed.get('start_minute', 0),
                end_hour=parsed['end_hour'],
                end_minute=parsed.get('end_minute', 0),
                weeks=parsed.get('recurring_weeks', 4)
            )
            say(result['message'])
        else:
            missing = []
            if not parsed['room_name']:
                missing.append("회의실")
            if parsed['recurring_weekday'] is None:
                missing.append("요일")
            if parsed['start_hour'] is None:
                missing.append("시간")

            say(
                f"반복 예약하려면 조금 더 정보가 필요해요! 🙏\n\n"
                f"*부족한 정보:* {', '.join(missing)}\n\n"
                "*예시:*\n"
                "• `매주 금요일 16~18시 뭄바이`\n"
                "• `매주 월요일 오전 10시~12시 델리`"
            )

    else:  # unknown
        say(
            "음... 무슨 말씀이신지 잘 모르겠어요 🤔\n\n"
            "`도움말` 이라고 하시면 제가 할 수 있는 것들을 알려드릴게요!"
        )


def register_message_handlers(app: App, reservation_service: ReservationService):
    """Register all message-related event handlers."""

    parser = IntentParser()

    @app.event("app_mention")
    def handle_app_mention(event, say, client, logger):
        """Handle @bot mentions."""
        text = event.get("text", "")
        user_id = event.get("user")
        user_name = get_user_display_name(client, user_id)

        logger.info(f"Received mention from {user_name} ({user_id}): {text}")

        # Remove bot mention from text
        clean_text = text.split(">", 1)[-1].strip() if ">" in text else text

        # 빈 메시지면 도움말 보여주기
        if not clean_text:
            say(get_help_message())
            return

        # Parse intent using LLM
        parsed = parser.parse(clean_text)
        logger.info(f"Parsed intent: {parsed['intent']}, data: {parsed}")

        # Handle intent
        handle_intent(parsed, user_id, user_name, reservation_service, say)

    @app.message()
    def handle_message(message, say, client, logger):
        """Handle direct messages (DM only)."""
        if message.get("bot_id") or message.get("thread_ts"):
            return

        text = message.get("text", "")
        user_id = message.get("user")
        user_name = get_user_display_name(client, user_id)

        logger.info(f"Received DM from {user_name} ({user_id}): {text}")

        parsed = parser.parse(text)

        # DM에서는 모든 의도에 응답 (unknown 포함)
        handle_intent(parsed, user_id, user_name, reservation_service, say)
