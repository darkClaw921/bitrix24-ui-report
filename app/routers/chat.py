"""Chat API router for FastAPI."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json

from app.config.database import get_database
from app.schemas.chat import (
    ChatMessageRequest, ChatResponse, ConversationCreate, 
    ConversationResponse, ConversationListResponse, MessageResponse
)
from app.services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_database)
):
    """Send a message to the chat and get a response."""
    try:
        response = await chat_service.send_message(request, db)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.post("/stream")
async def stream_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_database)
):
    """Stream a message response from the chat."""
    try:
        async def generate_stream():
            async for chunk in chat_service.stream_message(request, db):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream message: {str(e)}"
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_database)
):
    """Get list of conversations."""
    try:
        conversations = chat_service.get_conversations(db, skip=skip, limit=limit)
        total = len(conversations)  # Simplified - in production, you'd want a proper count query
        
        return ConversationListResponse(
            conversations=conversations,
            total=total,
            page=skip // limit + 1,
            per_page=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_database)
):
    """Create a new conversation."""
    try:
        conversation = chat_service.create_conversation(request, db)
        return conversation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_database)
):
    """Delete a conversation."""
    try:
        success = chat_service.delete_conversation(conversation_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_database)
):
    """Get all messages for a conversation."""
    try:
        messages = chat_service.get_conversation_messages(conversation_id, db)
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation messages: {str(e)}"
        )