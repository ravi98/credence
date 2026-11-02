import sqlite3
import os
import sys

# Ensure root directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, Base, SessionLocal
from models.user import User, UserRole

def migrate_users():
    old_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "credence_auth.db")
    if not os.path.exists(old_db_path):
        print("No legacy credence_auth.db found. Skipping user migration.")
        return

    # Ensure tables exist in target database
    Base.metadata.create_all(bind=engine)

    old_conn = sqlite3.connect(old_db_path)
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()

    old_cursor.execute("SELECT * FROM users")
    old_users = old_cursor.fetchall()
    print(f"Found {len(old_users)} users in legacy database.")

    db = SessionLocal()
    migrated = 0
    skipped = 0

    try:
        for row in old_users:
            existing = db.query(User).filter(User.id == row["id"]).first()
            if existing:
                skipped += 1
                continue

            new_user = User(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                password_hash=row["password_hash"],
                role=UserRole.CUSTOMER,
                auth_provider=row["auth_provider"] or "email",
                google_id=row["google_id"],
                avatar_url=row["avatar_url"]
            )
            db.add(new_user)
            migrated += 1

        db.commit()
        print(f"Migration completed! Migrated: {migrated}, Skipped (already exist): {skipped}")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()
        old_conn.close()

if __name__ == "__main__":
    migrate_users()

