"""Chat-related Pydantic schemas for API validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageRoleEnum(str, Enum):
    """Message role enumeration for API."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChartType(str, Enum):
    """Chart type enumeration."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"


class ChatMessageRequest(BaseModel):
    """Schema for sending a chat message."""
    message: str = Field(..., min_length=1, max_length=10000, description="The chat message content")
    conversation_id: Optional[str] = Field(None, description="Conversation ID, if None will create new conversation")
    provider: Optional[str] = Field("openai", description="LLM provider to use")
    model: Optional[str] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Temperature for response generation")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="Maximum tokens in response")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")


class ChartData(BaseModel):
    """Schema for chart data."""
    type: ChartType = Field(..., description="Type of chart")
    data: Dict[str, Any] = Field(..., description="Chart data")
    options: Optional[Dict[str, Any]] = Field(None, description="Chart display options")
    title: Optional[str] = Field(None, description="Chart title")


class MessageResponse(BaseModel):
    """Schema for a chat message response."""
    id: str = Field(..., description="Message ID")
    content: str = Field(..., description="Message content")
    role: MessageRoleEnum = Field(..., description="Message role")
    timestamp: datetime = Field(..., description="Message timestamp")
    provider: Optional[str] = Field(None, description="LLM provider used")
    model: Optional[str] = Field(None, description="Model used")
    conversation_id: str = Field(..., description="Conversation ID")
    chart_data: Optional[ChartData] = Field(None, description="Chart data if applicable")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Schema for chat API response."""
    message: MessageResponse = Field(..., description="Assistant's response message")
    conversation_id: str = Field(..., description="Conversation ID")
    success: bool = Field(True, description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if any")


class StreamChunk(BaseModel):
    """Schema for streaming response chunks."""
    content: str = Field(..., description="Chunk content")
    is_complete: bool = Field(False, description="Whether this is the final chunk")
    conversation_id: str = Field(..., description="Conversation ID")
    message_id: Optional[str] = Field(None, description="Message ID when complete")


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    title: Optional[str] = Field(None, description="Conversation title")
    provider: Optional[str] = Field("openai", description="Default LLM provider")
    model: Optional[str] = Field(None, description="Default model")
    settings: Optional[Dict[str, Any]] = Field(None, description="Provider-specific settings")


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    provider: Optional[str] = Field(None, description="Default LLM provider")
    model: Optional[str] = Field(None, description="Default model")
    message_count: int = Field(0, description="Number of messages in conversation")
    settings: Optional[Dict[str, Any]] = Field(None, description="Provider-specific settings")


class ConversationListResponse(BaseModel):
    """Schema for conversation list response."""
    conversations: List[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total number of conversations")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(20, description="Items per page")


class ProviderConfigRequest(BaseModel):
    """Schema for provider configuration request."""
    api_key: str = Field(..., min_length=10, description="API key for the provider")
    default_model: Optional[str] = Field(None, description="Default model to use for this provider")