from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Text, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())[:8])
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("ChatSession", back_populates="owner")

class ChatSession(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    filenames = Column(JSON, default=[])
    created_at = Column(Float, default=lambda: datetime.utcnow().timestamp())
    
    owner = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String) # user or assistant
    content = Column(Text)
    timestamp = Column(Float, default=lambda: datetime.utcnow().timestamp())

    session = relationship("ChatSession", back_populates="messages")
