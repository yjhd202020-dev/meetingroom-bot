"""
Meeting Room Reservation Slack Bot - Main Application
Runs in HTTP Mode for Railway deployment.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from models.database import Database
from services.reservation_service import ReservationService
from handlers.message_handler import register_message_handlers


# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Validate required environment variables
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

if not SLACK_BOT_TOKEN or not SLACK_SIGNING_SECRET:
    raise ValueError(
        "❌ Missing required environment variables!\n"
        "Please set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET in .env file"
    )

# Initialize Slack app (HTTP Mode)
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# Initialize database
db_path = os.environ.get("DATABASE_PATH", "./data/meetingroom.db")
print(f"📦 Using SQLite database: {db_path}")
db = Database(db_path)

# Initialize service layer
reservation_service = ReservationService(db)

# Register event handlers
register_message_handlers(app, reservation_service)

# Create FastAPI handler
handler = SlackRequestHandler(app)


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


# FastAPI application for HTTP Mode
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Create FastAPI app
api = FastAPI(title="Meeting Room Reservation Bot")

# Serve frontend static files
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    api.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")

# Health check endpoint for Railway
@api.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "meetingroom-bot",
        "database": db_path
    }

# Serve frontend index.html for root path
@api.get("/")
async def serve_frontend():
    """Serve the frontend calendar page."""
    index_path = frontend_build_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Frontend not built. Run 'cd frontend && npm run build'"}

# Slack events endpoint
@api.post("/slack/events")
async def slack_events(req: Request):
    """Handle Slack events."""
    return await handler.handle(req)

# Slack commands endpoint (for slash commands if needed)
@api.post("/slack/commands")
async def slack_commands(req: Request):
    """Handle Slack slash commands."""
    return await handler.handle(req)


def main():
    """Start the bot in HTTP Mode."""
    import uvicorn

    port = int(os.environ.get("PORT", 8080))

    print("🌐 Starting API server on port {}...".format(port))
    print("🤖 Starting Slack bot...")

    uvicorn.run(
        api,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
