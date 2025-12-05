"""
Meeting Room Reservation Slack Bot - Main Application
Runs in Socket Mode for local development and easy deployment.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from models.database import Database
from services.reservation_service import ReservationService
from handlers.message_handler import register_message_handlers


# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Validate required environment variables
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError(
        "❌ Missing required environment variables!\n"
        "Please set SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env file"
    )

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)

# Initialize database
db_path = os.environ.get("DATABASE_PATH", "./data/meetingroom.db")
db = Database(db_path)

# Initialize service layer
reservation_service = ReservationService(db)

# Register event handlers
register_message_handlers(app, reservation_service)


@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    """Update the App Home tab when user opens it."""
    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🏢 회의실 예약 시스템",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*사용 가능한 회의실:*\n• Delhi (델리)\n• Mumbai (뭄바이)\n• Chennai (첸나이)"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*예약 방법:*\n봇을 멘션하고 자연어로 요청하세요!\n\n예시:\n• `@봇 오후 4:00~6:00 Delhi 예약`\n• `@봇 내일 오전 10시~12시 Mumbai`\n• `@봇 12/10 14:00-16:00 Chennai`"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*예약 현황 확인:*\n• `@봇 전체 예약 현황`\n• `@봇 이번주 예약`"
                        }
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error updating home tab: {e}")


def main():
    """Start the bot in Socket Mode."""
    print("🤖 Starting Meeting Room Reservation Bot...")
    print(f"📍 Database: {db_path}")
    print(f"🔌 Socket Mode: Enabled")
    print("✅ Bot is running! Press Ctrl+C to stop.\n")

    # Start Socket Mode handler
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()


if __name__ == "__main__":
    main()
