# Meeting Room Reservation Slack Bot

> **Note**: This file serves as an index to guide you through the project documentation structure. Please refer to the linked documents below for detailed information.

---

## 📂 Document Structure

### 1. [README.md](README.md) - Project Overview and Quick Start

Provides project overview, installation instructions, and usage examples for the meeting room reservation Slack bot.

**Key Information**:
- Meeting rooms: Delhi, Mumbai, Chennai
- Core features: Natural language reservation, duplicate prevention, weekly view
- Tech stack: Python 3.10+, slack-bolt (Socket Mode), SQLite

### 2. [TODO.md](TODO.md) - Development Roadmap

Contains comprehensive development plan organized into 6 phases:
- Phase 1: Basic design and architecture
- Phase 2: Natural language processing module
- Phase 3: Reservation management system
- Phase 4: Slack bot integration
- Phase 5: Deployment and operations
- Phase 6: Advanced features (optional)

### 3. [docs/SLACK_SETUP.md](docs/SLACK_SETUP.md) - Slack App Configuration

Detailed guide for setting up the Slack app, including:
- Slack App creation and permissions
- Event subscriptions configuration
- Bot token setup

---

## 🎯 Project Structure

```
meetingroom/
├── src/                    # Main application code
│   ├── app.py             # Bot entry point
│   ├── handlers/          # Slack event handlers
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   └── utils/             # Utility functions
├── scripts/               # Initialization scripts
│   └── init_db.py         # Database setup
├── config/                # Configuration files
├── docs/                  # Documentation
├── data/                  # SQLite database storage
├── README.md              # Project overview
├── TODO.md                # Development roadmap
└── CLAUDE.md              # This file (documentation index)
```

---

## 🚀 Quick Commands

```bash
# Install dependencies
uv sync

# Initialize database
uv run python scripts/init_db.py

# Run the bot (Socket Mode)
uv run python src/app.py
```

---

## 🤖 Recommended Sidekick

**@slack-bot-config-master** - Slack Bot Configuration, GitHub Actions, and Deployment Expert

**Alternative Sidekicks**:
- `@developer` (dylan.min) - Agile development and task breakdown specialist
- `@alchemist` (neal.lee) - Infrastructure automation expert

---

**Project Type**: Slack Bot (Socket Mode)
**Primary Language**: Python
**Database**: SQLite (development), PostgreSQL (production)
**Created**: 2025-12-05
