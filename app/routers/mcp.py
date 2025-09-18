"""MCP server management API router for FastAPI."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.config.database import get_database
from app.schemas.mcp import (
    MCPServerCreate, MCPServerUpdate, MCPServerResponse,
    MCPServerListResponse, MCPServerConnectionTest, MCPServerTestResponse
)
from app.services.mcp_manager import mcp_manager
from app.services.mcp_client import mcp_client_service

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("/servers", response_model=MCPServerListResponse)
async def get_servers(db: Session = Depends(get_database)):
    """Get all MCP servers."""
    try:
        servers = mcp_manager.get_servers(db)
        return servers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get servers: {str(e)}"
        )


@router.post("/servers", response_model=MCPServerResponse)
async def create_server(
    request: MCPServerCreate,
    db: Session = Depends(get_database)
):
    """Create a new MCP server."""
    try:
        server = mcp_manager.create_server(request, db)
        return server
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create server: {str(e)}"
        )


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_server(
    server_id: str,
    db: Session = Depends(get_database)
):
    """Get a specific MCP server."""
    try:
        server = mcp_manager.get_server(server_id, db)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        return server
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server: {str(e)}"
        )


@router.put("/servers/{server_id}", response_model=MCPServerResponse)
async def update_server(
    server_id: str,
    request: MCPServerUpdate,
    db: Session = Depends(get_database)
):
    """Update an existing MCP server."""
    try:
        server = mcp_manager.update_server(server_id, request, db)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        return server
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update server: {str(e)}"
        )


@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: str,
    db: Session = Depends(get_database)
):
    """Delete an MCP server."""
    try:
        success = mcp_manager.delete_server(server_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        return {"message": "Server deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete server: {str(e)}"
        )


@router.post("/test-connection", response_model=MCPServerTestResponse)
async def test_connection(request: MCPServerConnectionTest):
    """Test connection to an MCP server."""
    try:
        endpoint = request.url or request.endpoint
        result = await mcp_manager.test_server_connection(
            endpoint=endpoint,
            configuration=request.configuration
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}"
        )


@router.post("/servers/{server_id}/execute")
async def execute_request(
    server_id: str,
    request_data: Dict[str, Any],
    db: Session = Depends(get_database)
):
    """Execute a request to an MCP server."""
    try:
        result = await mcp_manager.execute_mcp_request(server_id, request_data, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute request: {str(e)}"
        )


@router.get("/tools")
async def get_mcp_tools(db: Session = Depends(get_database)):
    """Return list of tools from all active MCP servers."""
    try:
        tools = await mcp_client_service.get_tools(db)
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tools: {str(e)}"
        )


@router.get("/prompts/{server_name}/{prompt_name}")
async def get_mcp_prompt(
    server_name: str,
    prompt_name: str,
    db: Session = Depends(get_database)
):
    """Return prompt from specified MCP server."""
    try:
        prompt = await mcp_client_service.get_prompt(db, server_name, prompt_name)
        return {"prompt": prompt}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt: {str(e)}"
        )