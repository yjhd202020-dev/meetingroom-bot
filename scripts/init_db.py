"""
Initialize the database for meeting room reservations.
"""
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.database import Database


def main():
    """Initialize database with schema and default data."""
    print("🗄️  Initializing meeting room database...")

    db = Database()

    # Get all rooms to verify initialization
    rooms = db.get_all_rooms()

    print(f"✅ Database initialized successfully!")
    print(f"📍 Database location: {db.db_path}")
    print(f"\n🏢 Available rooms:")
    for room in rooms:
        print(f"   - {room['name']}: {room['description']}")

    print("\n✨ Ready to start accepting reservations!")


if __name__ == "__main__":
    main()
