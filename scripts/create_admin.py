import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logger import logger
from app.models.user import User
from app.services.database import DatabaseService


async def create_admin_user():
    """Create an admin user."""
    try:
        # Initialize database service
        db_service = DatabaseService()

        # Check if admin user already exists
        existing_admin = await db_service.get_user_by_email("Isaque")
        if existing_admin:
            logger.info("Admin user already exists", extra={"email": "Isaque"})
            print("✅ Admin user 'Isaque' already exists!")
            return

        # Create admin user
        admin_user = await db_service.create_user(email="Isaque", password=User.hash_password("ifsp"), level="admin")

        logger.info(
            "Admin user created successfully",
            extra={"email": admin_user.email, "level": admin_user.level, "user_id": admin_user.id},
        )

        print("✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Level: {admin_user.level}")
        print(f"   ID: {admin_user.id}")

    except Exception as e:
        logger.error("Failed to create admin user", exc_info=True, extra={"error": str(e)})
        print(f"❌ Error creating admin user: {e}")
        # Don't exit the process; return so callers (like app startup) can continue.
        return


if __name__ == "__main__":
    print("Creating admin user...")
    asyncio.run(create_admin_user())
