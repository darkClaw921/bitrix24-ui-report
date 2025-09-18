"""Service wrapper for MultiServerMCPClient to use MCP servers from DB."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.models.mcp_server import MCPServer


class MCPClientService:
    """Builds a MultiServerMCPClient from active MCP servers in DB."""

    def _build_client(self, db: Session) -> MultiServerMCPClient:
        servers: List[MCPServer] = db.query(MCPServer).filter(MCPServer.active == True).all()
        server_map: Dict[str, Dict[str, Any]] = {}
        for server in servers:
            server_map[server.name] = {
                "url": server.url,
                "transport": server.transport or "sse",
                "env": server.env or {},
            }
        return MultiServerMCPClient(server_map)

    async def get_tools(self, db: Session) -> List[Dict[str, Any]]:
        client = self._build_client(db)
        return await client.get_tools()

    async def get_prompt(self, db: Session, server_name: str, prompt_name: str) -> Any:
        client = self._build_client(db)
        return await client.get_prompt(server_name, prompt_name)


# Global instance
mcp_client_service = MCPClientService()


