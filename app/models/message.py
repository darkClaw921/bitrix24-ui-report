"""Message SQLAlchemy model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum


class MessageRole(enum.Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """Message model for storing chat messages."""
    
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    provider = Column(String(50), nullable=True)  # LLM provider used
    model = Column(String(100), nullable=True)    # Model used for generation
    message_metadata = Column(JSON, nullable=True)        # Additional message metadata
    chart_data = Column(JSON, nullable=True)      # Chart information if applicable
    
    # Relationship with conversation
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role.value}, conversation_id={self.conversation_id})>"
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "content": self.content,
            "role": self.role.value,
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "model": self.model,
            "metadata": self.message_metadata,
            "chart_data": self.chart_data
        }