"""MCP server-related Pydantic schemas for API validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MCPServerCreate(BaseModel):
    """Schema for creating a new MCP server.

    Supports both legacy "endpoint" and new fields: "url", "transport", "env".
    """
    name: str = Field(..., min_length=1, max_length=255, description="Server display name")
    # New canonical fields
    url: Optional[str] = Field(None, min_length=1, max_length=500, description="Server URL")
    transport: Optional[str] = Field("sse", min_length=1, max_length=50, description="Transport type (e.g. sse, websocket)")
    env: Optional[Dict[str, Any]] = Field(None, description="Environment variables for the MCP server")
    # Legacy/compat
    endpoint: Optional[str] = Field(None, min_length=1, max_length=500, description="[Deprecated] Server URL or connection string")
    description: Optional[str] = Field(None, max_length=1000, description="Server description")
    active: Optional[bool] = Field(True, description="Whether the server is active")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Server-specific configuration or import payload")


class MCPServerUpdate(BaseModel):
    """Schema for updating an MCP server."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Server display name")
    # New canonical fields
    url: Optional[str] = Field(None, min_length=1, max_length=500, description="Server URL")
    transport: Optional[str] = Field(None, min_length=1, max_length=50, description="Transport type")
    env: Optional[Dict[str, Any]] = Field(None, description="Environment variables for the MCP server")
    # Legacy/compat
    endpoint: Optional[str] = Field(None, min_length=1, max_length=500, description="[Deprecated] Server URL or connection string")
    description: Optional[str] = Field(None, max_length=1000, description="Server description")
    active: Optional[bool] = Field(None, description="Whether the server is active")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Server-specific configuration")


class MCPServerResponse(BaseModel):
    """Schema for MCP server response."""
    id: str = Field(..., description="Server ID")
    name: str = Field(..., description="Server display name")
    url: str = Field(..., description="Server URL")
    transport: str = Field(..., description="Transport type")
    env: Optional[Dict[str, Any]] = Field(None, description="Environment variables for the MCP server")
    description: Optional[str] = Field(None, description="Server description")
    active: bool = Field(..., description="Whether the server is active")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Server-specific configuration")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class MCPServerListResponse(BaseModel):
    """Schema for MCP server list response."""
    servers: List[MCPServerResponse] = Field(..., description="List of MCP servers")
    total: int = Field(..., description="Total number of servers")
    active_count: int = Field(..., description="Number of active servers")


class MCPServerConnectionTest(BaseModel):
    """Schema for testing MCP server connection."""
    # Accept both for compatibility
    url: Optional[str] = Field(None, min_length=1, max_length=500, description="Server URL")
    endpoint: Optional[str] = Field(None, min_length=1, max_length=500, description="[Deprecated] Server URL or connection string")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Server-specific configuration")


class MCPServerTestResponse(BaseModel):
    """Schema for MCP server connection test response."""
    success: bool = Field(..., description="Whether the connection test was successful")
    message: str = Field(..., description="Test result message")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    capabilities: Optional[List[str]] = Field(None, description="Server capabilities if detected")