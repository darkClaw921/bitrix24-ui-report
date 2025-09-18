"""Configuration management API router."""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from app.config.config_manager import config_manager
from app.config.utils import get_system_info, validate_required_config, get_environment_name

router = APIRouter(prefix="/api/config", tags=["configuration"])


@router.get("/status")
async def get_configuration_status():
    """Get current configuration status."""
    try:
        runtime_status = config_manager.validate_runtime_config()
        return {
            "status": runtime_status["status"],
            "environment": get_environment_name(),
            "issues": runtime_status.get("issues", []),
            "warnings": runtime_status.get("warnings", []),
            "providers": {
                "available": config_manager.get_available_providers(),
                "count": len(config_manager.get_available_providers())
            },
            "features": {
                "database": runtime_status["status"] == "healthy",
                "websocket": True,
                "charts": True,
                "mcp": True
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration status: {str(e)}"
        )


@router.get("/summary")
async def get_configuration_summary():
    """Get configuration summary (safe for public exposure)."""
    try:
        return config_manager.export_config_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration summary: {str(e)}"
        )


@router.get("/providers")
async def get_provider_configurations():
    """Get available LLM provider configurations."""
    try:
        providers = {}
        for provider_name in ["openai", "grok", "anthropic"]:
            config = config_manager.get_provider_config(provider_name)
            if config:
                # Remove sensitive information
                safe_config = {
                    "name": provider_name,
                    "available": True,
                    "default_model": config.get("default_model"),
                    "supported": True
                }
                providers[provider_name] = safe_config
            else:
                providers[provider_name] = {
                    "name": provider_name,
                    "available": False,
                    "reason": "API key not configured"
                }
        
        return {
            "providers": providers,
            "total": len([p for p in providers.values() if p.get("available", False)])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provider configurations: {str(e)}"
        )


@router.get("/cors")
async def get_cors_configuration():
    """Get CORS configuration."""
    try:
        return config_manager.get_cors_config()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CORS configuration: {str(e)}"
        )


@router.get("/websocket")
async def get_websocket_configuration():
    """Get WebSocket configuration."""
    try:
        return config_manager.get_websocket_config()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket configuration: {str(e)}"
        )


@router.get("/charts")
async def get_chart_configuration():
    """Get chart generation configuration."""
    try:
        return config_manager.get_chart_config()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chart configuration: {str(e)}"
        )


@router.get("/database")
async def get_database_configuration():
    """Get database configuration (safe information only)."""
    try:
        config = config_manager.get_database_config()
        # Remove sensitive information
        safe_config = {
            "type": "SQLite" if "sqlite" in config["url"] else "Other",
            "echo": config.get("echo", False),
            "pool_settings": {
                "pre_ping": config.get("pool_pre_ping", True),
                "recycle": config.get("pool_recycle", 300)
            }
        }
        return safe_config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database configuration: {str(e)}"
        )


@router.get("/rate-limiting")
async def get_rate_limiting_configuration():
    """Get rate limiting configuration."""
    try:
        return config_manager.get_rate_limiting_config()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limiting configuration: {str(e)}"
        )


@router.get("/system-info")
async def get_system_information():
    """Get system information for debugging."""
    try:
        return get_system_info()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system information: {str(e)}"
        )


@router.post("/validate")
async def validate_configuration(required_keys: Dict[str, Any] = None):
    """Validate configuration with optional required keys."""
    try:
        if required_keys is None:
            required_keys = {
                "keys": ["DATABASE_URL", "LOG_LEVEL"]
            }
        
        validation_result = validate_required_config(required_keys.get("keys", []))
        
        return {
            "valid": validation_result["valid"],
            "missing_keys": validation_result["missing_keys"],
            "present_count": len(validation_result["present_keys"]),
            "total_required": len(required_keys.get("keys", []))
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configuration: {str(e)}"
        )