"""FastAPI LangChain Chatbot - Main application entry point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config.database import create_tables, get_database
from app.config.settings import settings
from app.routers import chat, mcp, config, conversations, providers
from app.routers.websocket import websocket_chat_endpoint
from app.services.llm_manager import llm_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting FastAPI LangChain Chatbot...")
    
    # Create database tables
    create_tables()
    print("Database tables created.")
    
    # Initialize LLM providers
    available_providers = llm_manager.get_available_providers()
    print(f"Initialized LLM providers: {available_providers}")
    
    yield
    
    # Shutdown
    print("Shutting down FastAPI LangChain Chatbot...")


# Create FastAPI application
app = FastAPI(
    title="FastAPI LangChain Chatbot",
    description="A modern chatbot with multi-provider LLM support, conversation management, MCP server integration, and automatic chart generation",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(mcp.router)
app.include_router(config.router)
app.include_router(providers.router)

# WebSocket endpoint
app.add_websocket_route("/ws/chat/{conversation_id}", websocket_chat_endpoint)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main chat interface."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "FastAPI LangChain Chatbot",
            "available_providers": llm_manager.get_available_providers()
        }
    )


@app.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request):
    """Conversations management page."""
    return templates.TemplateResponse(
        "conversations.html",
        {
            "request": request,
            "title": "Conversations - FastAPI LangChain Chatbot"
        }
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings and MCP server management page."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "title": "Settings - FastAPI LangChain Chatbot"
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = await llm_manager.health_check()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "llm_providers": health_status
    }


@app.get("/api/providers")
async def get_providers():
    """Get available LLM providers and their information."""
    return llm_manager.get_all_providers_info()


if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )