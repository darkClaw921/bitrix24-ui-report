"""Conversations API router for FastAPI."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_database
from app.schemas.chat import ConversationResponse, ConversationListResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    provider: Optional[str] = None,
    date_filter: Optional[str] = None,
    db: Session = Depends(get_database)
):
    """Get list of conversations with optional filtering."""
    try:
        conversations = chat_service.get_conversations(
            db, 
            skip=skip, 
            limit=limit,
            search=search,
            provider=provider,
            date_filter=date_filter
        )
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_database)
):
    """Get a specific conversation by ID."""
    try:
        conversation = chat_service.get_conversation(conversation_id, db)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.delete("/{conversation_id}")
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


@router.put("/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    title: str,
    db: Session = Depends(get_database)
):
    """Update conversation title."""
    try:
        success = chat_service.update_conversation_title(conversation_id, title, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"message": "Conversation title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation title: {str(e)}"
        )


@router.post("/bulk-delete")
async def bulk_delete_conversations(
    conversation_ids: List[str],
    db: Session = Depends(get_database)
):
    """Delete multiple conversations."""
    try:
        deleted_count = chat_service.bulk_delete_conversations(conversation_ids, db)
        return {
            "message": f"Successfully deleted {deleted_count} conversations",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversations: {str(e)}"
        )