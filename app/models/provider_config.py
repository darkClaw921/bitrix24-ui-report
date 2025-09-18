"""Provider configuration SQLAlchemy model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from app.config.database import Base


class ProviderConfig(Base):
    """Provider configuration model for storing LLM provider settings."""
    
    __tablename__ = "provider_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    provider_name = Column(String(50), nullable=False, index=True, unique=True)
    api_key = Column(Text, nullable=False)
    default_model = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ProviderConfig(id={self.id}, provider_name='{self.provider_name}', is_active={self.is_active})>"
    
    def to_dict(self):
        """Convert provider config to dictionary."""
        return {
            "id": str(self.id),
            "provider_name": self.provider_name,
            "default_model": self.default_model,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }