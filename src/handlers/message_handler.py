"""
Slack message event handlers.
"""
import os
from slack_bolt import App
from utils.nlp_parser import IntentParser
from services.reservation_service import ReservationService

# 웹 캘린더 URL
WEB_URL = os.environ.get("WEB_URL", "")


def get_help_message() -> str:
    """Return comprehensive help message."""
    msg = """안녕하세요!! 저 위저드예요~ 회의실 예약 도와드릴게요! 🙋‍♀️

*🏢 회의실은요~*
Delhi(델리), Mumbai(뭄바이), Chennai(첸나이) 이렇게 3개 있어요!

*📅 예약은 그냥 말로 하시면 돼요 ㅎㅎ*
• `내일 3시~5시 델리 잡아줘`
• `금요일 오후 2시부터 4시 뭄바이`
• `다음주 월요일 14~16시 첸나이`

*🔁 매주 정기 예약도 되구요!*
• `매주 금요일 16~18시 뭄바이`
• `매주 월요일 오전 10시 델리`

*📋 예약 확인하려면~*
• `이번주 뭐 있어?`
• `전체 예약 보여줘`
• `내 예약`

*❌ 취소는요~*
• `내 예약` 보고 → `3번 취소해줘`

아 그리고 그냥 아무 얘기나 해도 돼요!!
심심하면 말 걸어주세요 ㅋㅋㅋ 😊"""

    if WEB_URL:
        msg += f"\n\n*📊 웹 캘린더*\n한눈에 보려면 여기로~: {WEB_URL}"

    return msg


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

    # 일반 대화 응답 (ChatGPT처럼)
    if intent == 'chat':
        say(parsed.get('response', '넵넵! 뭐 도와드릴까요? ㅎㅎ'))
        return

    if intent == 'help':
        say(get_help_message())

    elif intent == 'status':
        status = reservation_service.get_weekly_status(parsed['week_offset'])
        if WEB_URL:
            status += f"\n\n📊 캘린더로 보기: {WEB_URL}"
        say(status)

    elif intent == 'all_reservations':
        status = reservation_service.get_all_reservations()
        if WEB_URL:
            status += f"\n\n📊 캘린더로 보기: {WEB_URL}"
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
                    "오 취소하시려구요? 어떤 거요?? 🤔\n\n"
                    f"{result['message']}\n\n"
                    "_몇 번 취소할지 알려주세요~ (예: `3번 취소`)_"
                )
            else:
                say("엥? 취소할 예약이 없는데요...?? 📭")

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
                missing.append("회의실")
            if not parsed['start_time']:
                missing.append("날짜랑 시간")

            say(
                f"앗 잠깐요!! {', '.join(missing)} 알려주셔야 해요 ㅠㅠ\n\n"
                "이렇게 말씀해주시면 돼요~\n"
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
                f"오 매주 예약이요?? 근데 {', '.join(missing)} 알려주셔야 해요!\n\n"
                "이렇게요~\n"
                "• `매주 금요일 16~18시 뭄바이`\n"
                "• `매주 월요일 오전 10시~12시 델리`"
            )

    else:  # unknown
        say(
            "앗 잠깐... 뭐라고 하셨죠?? 🤔\n\n"
            "`도움말` 하시면 제가 뭘 할 수 있는지 알려드릴게요~!"
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
