"""Chat service with conversation management and chart integration."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.chat import (
    ChatMessageRequest, ChatResponse, MessageResponse, 
    ConversationCreate, ConversationResponse, ChartData, MessageRoleEnum
)
from app.services.llm_manager import llm_manager
from app.services.chart_analyzer import chart_analyzer
from app.config.database import get_database


class ChatService:
    """Service for handling chat operations and conversation management."""
    
    def __init__(self):
        """Initialize chat service."""
        pass
    
    async def send_message(
        self,
        request: ChatMessageRequest,
        db: Session
    ) -> ChatResponse:
        """Send a message and get response from LLM."""
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                conversation_id=request.conversation_id,
                provider=request.provider,
                model=request.model,
                db=db
            )
            
            # Save user message
            user_message = self._save_message(
                conversation_id=conversation.id,
                content=request.message,
                role=MessageRole.USER,
                db=db
            )
            
            # Get conversation history
            messages = self._get_conversation_messages(conversation.id, db)
            
            # Check if chart is requested
            chart_data = None
            try:
                if chart_analyzer.detect_chart_request(request.message):
                    chart_requirements = chart_analyzer.extract_chart_requirements(request.message)
                    chart_data = await chart_analyzer.generate_chart_data(
                        user_message=request.message,
                        chart_requirements=chart_requirements,
                        provider_name=request.provider or "openai"
                    )
            except Exception as chart_error:
                print(f"Chart generation error: {chart_error}")
                # Continue without chart if chart generation fails
            
            # Generate LLM response
            langchain_messages = self._prepare_messages_for_llm(messages)
            
            try:
                response_content = await llm_manager.generate_response(
                    messages=langchain_messages,
                    provider_name=request.provider,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
            except Exception as llm_error:
                print(f"LLM generation error: {llm_error}")
                response_content = f"Извините, произошла ошибка при генерации ответа: {str(llm_error)}"
            
            # Save assistant message
            assistant_message = self._save_message(
                conversation_id=conversation.id,
                content=response_content,
                role=MessageRole.ASSISTANT,
                provider=request.provider,
                model=request.model,
                chart_data=chart_data.dict() if chart_data else None,
                db=db
            )
            
            # Update conversation
            conversation.updated_at = datetime.utcnow()
            if not conversation.title or conversation.title == "Новый диалог":
                conversation.title = self._generate_conversation_title(request.message)
            db.commit()
            
            # Create response
            message_response = MessageResponse(
                id=str(assistant_message.id),
                content=response_content,
                role=MessageRoleEnum.ASSISTANT,
                timestamp=assistant_message.timestamp,
                provider=request.provider,
                model=request.model,
                conversation_id=str(conversation.id),
                chart_data=chart_data
            )
            
            return ChatResponse(
                message=message_response,
                conversation_id=str(conversation.id),
                success=True
            )
            
        except Exception as e:
            print(f"Chat service error: {e}")
            return ChatResponse(
                message=None,
                conversation_id=request.conversation_id or "",
                success=False,
                error=str(e)
            )
    
    async def stream_message(
        self,
        request: ChatMessageRequest,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream message response from LLM."""
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                conversation_id=request.conversation_id,
                provider=request.provider,
                model=request.model,
                db=db
            )
            
            # Save user message
            user_message = self._save_message(
                conversation_id=conversation.id,
                content=request.message,
                role=MessageRole.USER,
                db=db
            )
            
            # Get conversation history
            messages = self._get_conversation_messages(conversation.id, db)
            langchain_messages = self._prepare_messages_for_llm(messages)
            
            # Check for chart request
            chart_data = None
            if chart_analyzer.detect_chart_request(request.message):
                chart_requirements = chart_analyzer.extract_chart_requirements(request.message)
                chart_data = await chart_analyzer.generate_chart_data(
                    user_message=request.message,
                    chart_requirements=chart_requirements,
                    provider_name=request.provider or "openai"
                )
            
            # Stream response
            full_content = ""
            async for chunk in llm_manager.stream_response(
                messages=langchain_messages,
                provider_name=request.provider,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                full_content += chunk
                yield {
                    "content": chunk,
                    "is_complete": False,
                    "conversation_id": str(conversation.id)
                }
            
            # Save complete assistant message
            assistant_message = self._save_message(
                conversation_id=conversation.id,
                content=full_content,
                role=MessageRole.ASSISTANT,
                provider=request.provider,
                model=request.model,
                chart_data=chart_data.dict() if chart_data else None,
                db=db
            )
            
            # Update conversation
            conversation.updated_at = datetime.utcnow()
            if not conversation.title or conversation.title == "Новый диалог":
                conversation.title = self._generate_conversation_title(request.message)
            db.commit()
            
            # Send final chunk
            yield {
                "content": "",
                "is_complete": True,
                "conversation_id": str(conversation.id),
                "message_id": str(assistant_message.id),
                "chart_data": chart_data.dict() if chart_data else None
            }
            
        except Exception as e:
            yield {
                "content": f"Error: {str(e)}",
                "is_complete": True,
                "conversation_id": request.conversation_id or "",
                "error": str(e)
            }
    
    async def _get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        provider: Optional[str],
        model: Optional[str],
        db: Session
    ) -> Conversation:
        """Get existing conversation or create new one."""
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if conversation:
                return conversation
        
        # Create new conversation
        conversation = Conversation(
            title="Новый диалог",
            provider=provider,
            model=model
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    def _save_message(
        self,
        conversation_id: str,
        content: str,
        role: MessageRole,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        chart_data: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Message:
        """Save message to database."""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            role=role,
            provider=provider,
            model=model,
            chart_data=chart_data
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    def _get_conversation_messages(self, conversation_id: str, db: Session) -> List[Message]:
        """Get all messages for a conversation."""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp).all()
    
    def _prepare_messages_for_llm(self, messages: List[Message]) -> List:
        """Prepare messages for LLM processing."""
        langchain_messages = []
        
        # Add system message
        langchain_messages.append(SystemMessage(
            content="Вы полезный AI-ассистент. Отвечайте на русском языке, если пользователь пишет на русском, или на английском, если пользователь пишет на английском. Если пользователь просит создать график или диаграмму, предоставьте данные в текстовом формате, так как система автоматически создаст визуализацию."
        ))
        
        # Add conversation messages (limit to last 20 messages for context)
        recent_messages = messages[-20:] if len(messages) > 20 else messages
        
        for message in recent_messages:
            if message.role == MessageRole.USER:
                langchain_messages.append(HumanMessage(content=message.content))
            elif message.role == MessageRole.ASSISTANT:
                langchain_messages.append(AIMessage(content=message.content))
        
        return langchain_messages
    
    def _generate_conversation_title(self, first_message: str) -> str:
        """Generate a title for the conversation based on the first message."""
        # Simple title generation - take first 50 characters
        title = first_message.strip()[:50]
        if len(first_message) > 50:
            title += "..."
        return title
    
    def get_conversations(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        provider: Optional[str] = None,
        date_filter: Optional[str] = None
    ) -> List[ConversationResponse]:
        """Get list of conversations with optional filtering."""
        query = db.query(Conversation)
        
        # Apply search filter
        if search:
            query = query.filter(
                Conversation.title.contains(search)
            )
        
        # Apply provider filter
        if provider:
            query = query.filter(
                Conversation.provider == provider
            )
        
        # Apply date filter
        if date_filter:
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            
            if date_filter == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Conversation.updated_at >= start_date)
            elif date_filter == "week":
                start_date = now - timedelta(days=7)
                query = query.filter(Conversation.updated_at >= start_date)
            elif date_filter == "month":
                start_date = now - timedelta(days=30)
                query = query.filter(Conversation.updated_at >= start_date)
        
        conversations = query.order_by(
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                provider=conv.provider,
                model=conv.model,
                message_count=len(conv.messages) if conv.messages else 0,
                settings=conv.settings
            )
            for conv in conversations
        ]
    
    def create_conversation(self, request: ConversationCreate, db: Session) -> ConversationResponse:
        """Create a new conversation."""
        conversation = Conversation(
            title=request.title or "Новый диалог",
            provider=request.provider,
            model=request.model,
            settings=request.settings
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            provider=conversation.provider,
            model=conversation.model,
            message_count=0,
            settings=conversation.settings
        )
    
    def get_conversation(self, conversation_id: str, db: Session) -> Optional[ConversationResponse]:
        """Get a specific conversation by ID."""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
            
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            provider=conversation.provider,
            model=conversation.model,
            message_count=len(conversation.messages) if conversation.messages else 0,
            settings=conversation.settings
        )
    
    def update_conversation_title(self, conversation_id: str, title: str, db: Session) -> bool:
        """Update conversation title."""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    
    def bulk_delete_conversations(self, conversation_ids: List[str], db: Session) -> int:
        """Delete multiple conversations."""
        deleted_count = 0
        
        for conversation_id in conversation_ids:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if conversation:
                db.delete(conversation)
                deleted_count += 1
        
        db.commit()
        return deleted_count

    def delete_conversation(self, conversation_id: str, db: Session) -> bool:
        """Delete a conversation and all its messages."""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        db: Session
    ) -> List[MessageResponse]:
        """Get all messages for a conversation."""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp).all()
        
        return [
            MessageResponse(
                id=str(msg.id),
                content=msg.content,
                role=MessageRoleEnum(msg.role.value),
                timestamp=msg.timestamp,
                provider=msg.provider,
                model=msg.model,
                conversation_id=str(msg.conversation_id),
                chart_data=ChartData(**msg.chart_data) if msg.chart_data else None,
                metadata=msg.message_metadata
            )
            for msg in messages
        ]


# Global chat service instance
chat_service = ChatService()