"""MCP server management service."""

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.mcp_server import MCPServer
from app.schemas.mcp import (
    MCPServerCreate, MCPServerUpdate, MCPServerResponse, 
    MCPServerListResponse, MCPServerTestResponse
)
import httpx
import asyncio


class MCPManager:
    """Manager for MCP (Model Context Protocol) servers."""
    
    def __init__(self):
        """Initialize MCP manager."""
        pass
    
    def create_server(self, request: MCPServerCreate, db: Session) -> MCPServerResponse:
        """Create a new MCP server.

        Accepts legacy "endpoint" or new fields (url, transport, env).
        """
        url = request.url or request.endpoint
        transport = request.transport or "sse"

        server = MCPServer(
            name=request.name,
            url=url,
            transport=transport,
            env=request.env,
            description=request.description,
            active=request.active,
            configuration=request.configuration,
        )
        db.add(server)
        db.commit()
        db.refresh(server)
        
        return MCPServerResponse(
            id=str(server.id),
            name=server.name,
            url=server.url,
            transport=server.transport,
            env=server.env,
            description=server.description,
            active=server.active,
            configuration=server.configuration,
            created_at=server.created_at,
            updated_at=server.updated_at,
        )
    
    def get_servers(self, db: Session) -> MCPServerListResponse:
        """Get all MCP servers."""
        servers = db.query(MCPServer).order_by(MCPServer.created_at.desc()).all()
        
        server_responses = [
            MCPServerResponse(
                id=str(server.id),
                name=server.name,
                url=server.url,
                transport=server.transport,
                env=server.env,
                description=server.description,
                active=server.active,
                configuration=server.configuration,
                created_at=server.created_at,
                updated_at=server.updated_at,
            )
            for server in servers
        ]
        
        active_count = len([s for s in servers if s.active])
        
        return MCPServerListResponse(
            servers=server_responses,
            total=len(servers),
            active_count=active_count
        )
    
    def get_server(self, server_id: str, db: Session) -> Optional[MCPServerResponse]:
        """Get a specific MCP server by ID."""
        server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
        
        if server:
            return MCPServerResponse(
                id=str(server.id),
                name=server.name,
                url=server.url,
                transport=server.transport,
                env=server.env,
                description=server.description,
                active=server.active,
                configuration=server.configuration,
                created_at=server.created_at,
                updated_at=server.updated_at,
            )
        return None
    
    def update_server(
        self, 
        server_id: str, 
        request: MCPServerUpdate, 
        db: Session
    ) -> Optional[MCPServerResponse]:
        """Update an existing MCP server."""
        server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
        
        if not server:
            return None
        
        # Update fields if provided
        if request.name is not None:
            server.name = request.name
        # URL / transport / env updates with legacy compatibility
        if request.url is not None:
            server.url = request.url
        elif request.endpoint is not None:
            server.url = request.endpoint
        if request.transport is not None:
            server.transport = request.transport
        if request.env is not None:
            server.env = request.env
        if request.description is not None:
            server.description = request.description
        if request.active is not None:
            server.active = request.active
        if request.configuration is not None:
            server.configuration = request.configuration
        
        db.commit()
        db.refresh(server)
        
        return MCPServerResponse(
            id=str(server.id),
            name=server.name,
            url=server.url,
            transport=server.transport,
            env=server.env,
            description=server.description,
            active=server.active,
            configuration=server.configuration,
            created_at=server.created_at,
            updated_at=server.updated_at,
        )
    
    def delete_server(self, server_id: str, db: Session) -> bool:
        """Delete an MCP server."""
        server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
        
        if server:
            db.delete(server)
            db.commit()
            return True
        return False
    
    async def test_server_connection(
        self, 
        endpoint: str, 
        configuration: Optional[Dict[str, Any]] = None
    ) -> MCPServerTestResponse:
        """Test connection to an MCP server."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            headers = {"Accept": "text/event-stream"}
            timeout = httpx.Timeout(connect=10.0, read=0.1)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                # Open SSE stream and determine success by response headers without reading body
                async with client.stream("GET", endpoint, headers=headers) as response:
                    end_time = asyncio.get_event_loop().time()
                    response_time = (end_time - start_time) * 1000  # ms

                    content_type = response.headers.get("content-type", "").lower()
                    if response.status_code < 400 and ("text/event-stream" in content_type or content_type == ""):
                        return MCPServerTestResponse(
                            success=True,
                            message="Connection successful (SSE headers received)",
                            response_time_ms=response_time,
                            capabilities=["sse_connectivity"]
                        )
                    return MCPServerTestResponse(
                        success=False,
                        message=f"HTTP {response.status_code}, Content-Type: {content_type or 'unknown'}",
                        response_time_ms=response_time
                    )
                    
        except asyncio.TimeoutError:
            return MCPServerTestResponse(
                success=False,
                message="Connection timeout"
            )
        except httpx.ConnectError as e:
            return MCPServerTestResponse(
                success=False,
                message=f"Connect error: {str(e)}"
            )
        except httpx.ReadTimeout as e:
            return MCPServerTestResponse(
                success=False,
                message=f"Read timeout: {str(e)}"
            )
        except httpx.HTTPError as e:
            return MCPServerTestResponse(
                success=False,
                message=f"HTTP error: {str(e)}"
            )
    
    def get_active_servers(self, db: Session) -> List[MCPServerResponse]:
        """Get all active MCP servers."""
        servers = db.query(MCPServer).filter(MCPServer.active == True).all()
        
        return [
            MCPServerResponse(
                id=str(server.id),
                name=server.name,
                url=server.url,
                transport=server.transport,
                env=server.env,
                description=server.description,
                active=server.active,
                configuration=server.configuration,
                created_at=server.created_at,
                updated_at=server.updated_at,
            )
            for server in servers
        ]
    
    async def execute_mcp_request(
        self,
        server_id: str,
        request_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Execute a request to an MCP server."""
        server = db.query(MCPServer).filter(
            MCPServer.id == server_id,
            MCPServer.active == True
        ).first()
        
        if not server:
            return {
                "success": False,
                "error": "Server not found or inactive"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # In a real implementation, this would use the MCP protocol
                # For now, it's a placeholder for HTTP-based communication
                response = await client.post(
                    server.url,
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json(),
                        "server_name": server.name
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Server returned {response.status_code}: {response.text}",
                        "server_name": server.name
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "server_name": server.name
            }


# Global MCP manager instance
mcp_manager = MCPManager()