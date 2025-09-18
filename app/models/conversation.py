"""Conversation SQLAlchemy model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.config.database import Base


class Conversation(Base):
    """Conversation model for storing chat conversations."""
    
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    provider = Column(String(50), nullable=True)  # Default LLM provider
    model = Column(String(100), nullable=True)    # Default model name
    settings = Column(JSON, nullable=True)        # Provider-specific settings
    
    # Relationship with messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}')>"
    
    def to_dict(self):
        """Convert conversation to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "provider": self.provider,
            "model": self.model,
            "settings": self.settings,
            "message_count": len(self.messages) if self.messages else 0
        }