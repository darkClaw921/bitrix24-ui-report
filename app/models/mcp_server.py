"""MCP Server SQLAlchemy model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from app.config.database import Base


class MCPServer(Base):
    """MCP Server model for storing MCP server configurations."""
    
    __tablename__ = "mcp_servers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False, index=True)
    url = Column(String(500), nullable=False)  # Server URL
    transport = Column(String(50), nullable=False, default="sse")  # Transport type (sse, websocket, etc.)
    env = Column(JSON, nullable=True)  # Environment variables
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    configuration = Column(JSON, nullable=True)  # Server-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<MCPServer(id={self.id}, name='{self.name}', active={self.active})>"
    
    def to_dict(self):
        """Convert MCP server to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "url": self.url,
            "transport": self.transport,
            "env": self.env,
            "description": self.description,
            "active": self.active,
            "configuration": self.configuration,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }