from typing import Dict, List, Optional, Any
import time
from multi_doc_chat.logger import GLOBAL_LOGGER as log
from .db import SessionLocal
from .models import ChatSession, ChatMessage

class SessionStore:
    """
    PostgreSQL-based persistent session storage.
    """
    
    DEFAULT_TTL = 86400  # 24 hours in seconds
    
    def __init__(self, ttl: int = DEFAULT_TTL):
        self.ttl = ttl
        log.info("SessionStore initialized (PostgreSQL)", ttl=ttl)
    
    def _is_expired(self, created_at: float) -> bool:
        """Check if a session has expired."""
        return time.time() - created_at > self.ttl
    
    def exists(self, session_id: str) -> bool:
        """Check if a valid (non-expired) session exists."""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                return False
            if self._is_expired(session.created_at):
                self.delete(session_id)
                return False
            return True
        finally:
            db.close()
    
    def create(self, session_id: str, user_id: str, filenames: List[str] = None) -> None:
        """Create a new session associated with a user."""
        db = SessionLocal()
        try:
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                filenames=filenames or []
            )
            db.add(session)
            db.commit()
            log.info("Session created (DB)", session_id=session_id, user_id=user_id)
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get chat history for a session."""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session or self._is_expired(session.created_at):
                return []
            
            return [{"role": m.role, "content": m.content} for m in session.messages]
        finally:
            db.close()
    
    def get_owner(self, session_id: str) -> Optional[str]:
        """Get the user_id owner of a session."""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            return session.user_id if session else None
        finally:
            db.close()

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions owned by a user."""
        db = SessionLocal()
        try:
            sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
            result = []
            for s in sessions:
                if not self._is_expired(s.created_at):
                    result.append({
                        "session_id": s.id,
                        "created_at": s.created_at,
                        "filenames": s.filenames,
                        "message_count": len(s.messages)
                    })
            return sorted(result, key=lambda x: x["created_at"], reverse=True)
        finally:
            db.close()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to session history."""
        db = SessionLocal()
        try:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content
            )
            db.add(message)
            db.commit()
        except Exception as e:
            db.rollback()
            log.error("Failed to add message to DB", session_id=session_id, error=str(e))
        finally:
            db.close()
    
    def delete(self, session_id: str) -> None:
        """Delete a session."""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                db.delete(session)
                db.commit()
                log.info("Session deleted (DB)", session_id=session_id)
        except Exception as e:
            db.rollback()
            log.error("Failed to delete session from DB", session_id=session_id, error=str(e))
        finally:
            db.close()
    
    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        db = SessionLocal()
        try:
            # This is a bit inefficient for large DBs, but matches original logic
            sessions = db.query(ChatSession).all()
            removed = 0
            for s in sessions:
                if self._is_expired(s.created_at):
                    db.delete(s)
                    removed += 1
            db.commit()
            if removed > 0:
                log.info("Expired sessions cleaned up (DB)", count=removed)
            return removed
        finally:
            db.close()

# Singleton instance for the application
session_store = SessionStore()
