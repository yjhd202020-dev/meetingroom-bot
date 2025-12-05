"""
Main entry point for Railway deployment.
Runs both Slack bot and FastAPI server.
"""
import os
import sys
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


def run_slack_bot():
    """Run Slack bot in Socket Mode."""
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
    from models.database import Database
    from services.reservation_service import ReservationService
    from handlers.message_handler import register_message_handlers

    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
    SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        print("⚠️ Slack tokens not configured, skipping bot startup")
        return

    app = App(token=SLACK_BOT_TOKEN)
    db = Database()
    reservation_service = ReservationService(db)
    register_message_handlers(app, reservation_service)

    print("🤖 Starting Slack bot...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()


def run_api_server():
    """Run FastAPI server."""
    import uvicorn
    from api import app

    port = int(os.environ.get("PORT", 8000))
    print(f"🌐 Starting API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    """Main entry point - runs both services."""
    mode = os.environ.get("RUN_MODE", "all")

    if mode == "bot":
        # Only run Slack bot
        run_slack_bot()
    elif mode == "api":
        # Only run API server
        run_api_server()
    else:
        # Run both (default for Railway)
        # Start Slack bot in a separate thread
        bot_thread = threading.Thread(target=run_slack_bot, daemon=True)
        bot_thread.start()

        # Run API server in main thread (required for Railway health checks)
        run_api_server()


if __name__ == "__main__":
    main()
