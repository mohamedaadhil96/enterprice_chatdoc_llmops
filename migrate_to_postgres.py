import json
import os
from pathlib import Path
from datetime import datetime
from multi_doc_chat.utils.db import SessionLocal, init_db
from multi_doc_chat.utils.models import User, ChatSession, ChatMessage

def migrate():
    print("🚀 Starting migration from JSON to PostgreSQL...")
    init_db()
    db = SessionLocal()
    
    # 1. Migrate Users
    users_file = Path("users/users.json")
    if users_file.exists():
        print("👤 Migrating users...")
        users_data = json.loads(users_file.read_text(encoding="utf-8"))
        for email, data in users_data.items():
            if not db.query(User).filter(User.email == email).first():
                user = User(
                    id=data["id"],
                    email=email,
                    name=data["name"],
                    password_hash=data["password_hash"],
                    created_at=datetime.fromisoformat(data["created_at"])
                )
                db.add(user)
        db.commit()

    # 2. Migrate Sessions
    sessions_dir = Path("sessions")
    if sessions_dir.exists():
        print("📂 Migrating sessions...")
        for sess_file in sessions_dir.glob("*.json"):
            try:
                data = json.loads(sess_file.read_text(encoding="utf-8"))
                session_id = data["session_id"]
                
                if not db.query(ChatSession).filter(ChatSession.id == session_id).first():
                    session = ChatSession(
                        id=session_id,
                        user_id=data["user_id"],
                        filenames=data.get("filenames", []),
                        created_at=data["created_at"]
                    )
                    db.add(session)
                    
                    # Migrate History
                    for msg in data.get("history", []):
                        chat_msg = ChatMessage(
                            session_id=session_id,
                            role=msg["role"],
                            content=msg["content"]
                        )
                        db.add(chat_msg)
            except Exception as e:
                print(f"❌ Error migrating session {sess_file.name}: {e}")
        db.commit()

    db.close()
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
