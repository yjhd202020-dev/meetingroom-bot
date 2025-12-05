"""
Slack message event handlers.
"""
import re
from slack_bolt import App
from utils.nlp_parser import ReservationParser, is_status_request, is_cancel_request, is_my_reservations_request
from services.reservation_service import ReservationService


def get_user_display_name(client, user_id: str) -> str:
    """Get user's display name from Slack API."""
    try:
        result = client.users_info(user=user_id)
        if result["ok"]:
            user = result["user"]
            # Priority: display_name > real_name > name
            profile = user.get("profile", {})
            display_name = profile.get("display_name") or profile.get("real_name") or user.get("name", "Unknown")
            return display_name
    except Exception as e:
        print(f"Error fetching user info: {e}")
    return "Unknown"


def extract_reservation_id(text: str) -> int | None:
    """Extract reservation ID from cancel request text."""
    # Pattern: "5 취소", "5번 취소", "#5 취소", "예약 5 취소"
    patterns = [
        r'(\d+)\s*번?\s*취소',
        r'#(\d+)\s*취소',
        r'취소\s*(\d+)',
        r'cancel\s*(\d+)',
        r'(\d+)\s*cancel',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def register_message_handlers(app: App, reservation_service: ReservationService):
    """Register all message-related event handlers."""

    parser = ReservationParser()

    @app.event("app_mention")
    def handle_app_mention(event, say, client, logger):
        """Handle @bot mentions."""
        text = event.get("text", "")
        user_id = event.get("user")

        # Get user display name from Slack API
        user_name = get_user_display_name(client, user_id)

        logger.info(f"Received mention from {user_name} ({user_id}): {text}")

        # Remove bot mention from text for parsing
        # Format: "<@U123456> 오후 4시~6시 Delhi 예약"
        clean_text = text.split(">", 1)[-1].strip() if ">" in text else text

        # Check if status request
        if is_status_request(clean_text):
            status = reservation_service.get_weekly_status()
            say(status)
            return

        # Check if my reservations request
        if is_my_reservations_request(clean_text):
            result = reservation_service.get_user_reservations(user_id)
            say(result['message'])
            return

        # Check if cancel request
        if is_cancel_request(clean_text):
            reservation_id = extract_reservation_id(clean_text)

            if reservation_id:
                # Cancel specific reservation
                result = reservation_service.cancel_reservation(reservation_id, user_id)
                say(result['message'])
            else:
                # Show user's reservations to help them cancel
                result = reservation_service.get_user_reservations(user_id)
                if result['reservations']:
                    say(result['message'])
                else:
                    say("📭 취소할 예약이 없습니다.")
            return

        # Try to parse reservation request
        parsed = parser.parse(clean_text)

        if not parsed:
            say(
                "죄송합니다. 요청을 이해하지 못했습니다. 😅\n\n"
                "*예약 방법:*\n"
                "• `@봇 오후 4:00~6:00 Delhi 예약`\n"
                "• `@봇 내일 오전 10시~12시 Mumbai`\n"
                "• `@봇 12월 10일 14:00-16:00 Chennai`\n\n"
                "*예약 현황 확인:*\n"
                "• `@봇 전체 예약 현황`\n"
                "• `@봇 내 예약`\n\n"
                "*예약 취소:*\n"
                "• `@봇 내 예약` → `@봇 [번호] 취소`"
            )
            return

        # Create reservation
        result = reservation_service.create_reservation(
            room_name=parsed['room_name'],
            slack_user_id=user_id,
            slack_username=user_name,
            start_time=parsed['start_time'],
            end_time=parsed['end_time']
        )

        say(result['message'])

    @app.message()
    def handle_message(message, say, client, logger):
        """
        Handle direct messages in the channel.
        Only processes messages in allowed channels (if configured).
        """
        # Skip bot messages and threaded replies
        if message.get("bot_id") or message.get("thread_ts"):
            return

        text = message.get("text", "")
        user_id = message.get("user")

        # Get user display name from Slack API
        user_name = get_user_display_name(client, user_id)

        logger.info(f"Received message from {user_name} ({user_id}): {text}")

        # Check if status request
        if is_status_request(text):
            status = reservation_service.get_weekly_status()
            say(status)
            return

        # Check if my reservations request
        if is_my_reservations_request(text):
            result = reservation_service.get_user_reservations(user_id)
            say(result['message'])
            return

        # Check if cancel request
        if is_cancel_request(text):
            reservation_id = extract_reservation_id(text)

            if reservation_id:
                result = reservation_service.cancel_reservation(reservation_id, user_id)
                say(result['message'])
            else:
                result = reservation_service.get_user_reservations(user_id)
                if result['reservations']:
                    say(result['message'])
                else:
                    say("📭 취소할 예약이 없습니다.")
            return

        # Try to parse reservation request
        parsed = parser.parse(text)

        if parsed:
            # Create reservation
            result = reservation_service.create_reservation(
                room_name=parsed['room_name'],
                slack_user_id=user_id,
                slack_username=user_name,
                start_time=parsed['start_time'],
                end_time=parsed['end_time']
            )

            say(result['message'])
