"""
Slack message event handlers.
"""
from slack_bolt import App
from utils.nlp_parser import IntentParser
from services.reservation_service import ReservationService


def get_help_message() -> str:
    """Return comprehensive help message with all bot capabilities."""
    return """🏢 *회의실 예약 봇 사용 가이드* 🤖

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 *이용 가능한 회의실*
• Delhi (델리)
• Mumbai (뭄바이)
• Chennai (첸나이)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 *예약하기*
자연어로 편하게 말씀하세요!

• `@봇 오후 4시~6시 Delhi 예약`
• `@봇 내일 오전 10시~12시 뭄바이`
• `@봇 다음주 화요일 14:00-16:00 첸나이`
• `@봇 12월 10일 3시~5시 델리`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔁 *반복 예약* (매주 정기 예약)
4주간 자동으로 예약됩니다!

• `@봇 매주 금요일 16:00~18:00 Mumbai`
• `@봇 매주 월요일 오전 10시~12시 Delhi`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 *예약 현황 보기*

• `@봇 이번주 예약 현황` - 이번주 예약
• `@봇 다음주 예약 현황` - 다음주 예약
• `@봇 전체 예약 현황` - 모든 예약 보기
• `@봇 내 예약` - 내가 한 예약만 보기

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ *예약 취소하기*

1. 먼저 `@봇 내 예약` 으로 예약 번호 확인
2. `@봇 [번호] 취소` (예: `@봇 5 취소`)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *팁*
• 시간은 "오후 3시", "15:00", "3pm" 모두 인식해요
• 회의실 이름은 영어/한글 모두 OK
• 자연스럽게 말해도 이해해요!

_언제든 `@봇 도움말` 로 이 안내를 다시 볼 수 있어요_ 😊"""


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

    if intent == 'status':
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
            result = reservation_service.get_user_reservations(user_id)
            if result['reservations']:
                say(result['message'])
            else:
                say("📭 취소할 예약이 없습니다.")

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
            say(
                "죄송합니다. 예약 정보가 부족합니다. 😅\n\n"
                "*예약 방법:*\n"
                "• `@봇 오후 4:00~6:00 Delhi 예약`\n"
                "• `@봇 내일 오전 10시~12시 Mumbai`\n"
                "• `@봇 다음주 화요일 14:00-16:00 Chennai`"
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
            say(
                "죄송합니다. 반복 예약 정보가 부족합니다. 😅\n\n"
                "*반복 예약 방법:*\n"
                "• `@봇 매주 금요일 16:00~18:00 Mumbai`\n"
                "• `@봇 매주 월요일 오전 10시~12시 Delhi`"
            )

    elif intent == 'help':
        say(get_help_message())

    else:  # unknown
        say(
            "죄송합니다. 요청을 이해하지 못했습니다. 😅\n\n"
            "`@봇 도움말` 을 입력하면 사용법을 볼 수 있어요!"
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

        logger.info(f"Received message from {user_name} ({user_id}): {text}")

        parsed = parser.parse(text)

        # Only respond to recognized intents in DM
        if parsed['intent'] != 'unknown':
            handle_intent(parsed, user_id, user_name, reservation_service, say)
