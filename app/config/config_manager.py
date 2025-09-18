"""Enhanced configuration manager for the FastAPI LangChain Chatbot."""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.config.settings import settings, OpenAIConfig, GrokConfig, AnthropicConfig


class ConfigurationManager:
    """Enhanced configuration manager for application settings."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.settings = settings
        self.logger = self._setup_logging()
        self._validate_environment()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup application logging."""
        logger = logging.getLogger("fastapi_langchain_chatbot")
        logger.setLevel(getattr(logging, self.settings.log_level.upper(), logging.INFO))
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler for errors
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(logs_dir / "application.log")
            file_handler.setLevel(logging.ERROR)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _validate_environment(self) -> None:
        """Validate environment configuration."""
        self.logger.info("Validating environment configuration...")
        
        # Check required directories
        required_dirs = ["logs", "static", "templates"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                self.logger.warning(f"Directory {dir_name} does not exist, creating...")
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # Validate API keys
        self._validate_api_keys()
        
        # Validate database
        self._validate_database_config()
        
        self.logger.info("Environment validation completed.")
    
    def _validate_api_keys(self) -> None:
        """Validate API key configurations."""
        api_keys = {
            "OpenAI": self.settings.openai_api_key,
            "Grok": self.settings.grok_api_key,
            "Anthropic": self.settings.anthropic_api_key
        }
        
        available_providers = []
        for provider, api_key in api_keys.items():
            if api_key and api_key != f"your_{provider.lower()}_api_key_here":
                available_providers.append(provider)
                self.logger.info(f"{provider} API key configured")
            else:
                self.logger.warning(f"{provider} API key not configured")
        
        if not available_providers:
            self.logger.warning("No LLM provider API keys configured. Chat functionality will be limited.")
        else:
            self.logger.info(f"Available LLM providers: {', '.join(available_providers)}")
    
    def _validate_database_config(self) -> None:
        """Validate database configuration."""
        db_url = self.settings.database_url
        
        if db_url.startswith("sqlite"):
            db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
            if db_path.startswith("./"):
                db_path = db_path[2:]
            
            db_dir = Path(db_path).parent
            if not db_dir.exists():
                self.logger.info(f"Creating database directory: {db_dir}")
                db_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Database configured: {db_url}")
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific LLM provider."""
        provider_configs = {
            "openai": self._get_openai_config,
            "grok": self._get_grok_config,
            "anthropic": self._get_anthropic_config
        }
        
        config_func = provider_configs.get(provider_name.lower())
        if config_func:
            return config_func()
        
        return None
    
    def _get_openai_config(self) -> Optional[Dict[str, Any]]:
        """Get OpenAI provider configuration."""
        if not self.settings.openai_api_key or self.settings.openai_api_key == "your_openai_api_key_here":
            return None
        
        return {
            "api_key": self.settings.openai_api_key,
            "default_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    
    def _get_grok_config(self) -> Optional[Dict[str, Any]]:
        """Get Grok provider configuration."""
        if not self.settings.grok_api_key or self.settings.grok_api_key == "your_grok_api_key_here":
            return None
        
        return {
            "api_key": self.settings.grok_api_key,
            "base_url": "https://api.x.ai/v1",
            "default_model": "grok-beta",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    
    def _get_anthropic_config(self) -> Optional[Dict[str, Any]]:
        """Get Anthropic provider configuration."""
        if not self.settings.anthropic_api_key or self.settings.anthropic_api_key == "your_anthropic_api_key_here":
            return None
        
        return {
            "api_key": self.settings.anthropic_api_key,
            "default_model": "claude-3-sonnet-20240229",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers."""
        available = []
        
        for provider in ["openai", "grok", "anthropic"]:
            if self.get_provider_config(provider):
                available.append(provider)
        
        return available
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration."""
        return {
            "allow_origins": self.settings.cors_origins,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }
    
    def get_websocket_config(self) -> Dict[str, Any]:
        """Get WebSocket configuration."""
        return {
            "timeout": self.settings.websocket_timeout,
            "ping_interval": 30,
            "ping_timeout": 10
        }
    
    def get_chart_config(self) -> Dict[str, Any]:
        """Get chart generation configuration."""
        return {
            "max_data_points": self.settings.max_chart_data_points,
            "default_type": self.settings.default_chart_type,
            "supported_types": ["line", "bar", "pie", "scatter", "area"],
            "colors": {
                "primary": "#2563eb",
                "secondary": "#3b82f6",
                "accent": "#60a5fa",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444"
            }
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "url": self.settings.database_url,
            "echo": self.settings.debug,
            "pool_pre_ping": True,
            "pool_recycle": 300
        }
    
    def get_rate_limiting_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return {
            "requests_per_minute": self.settings.rate_limit_per_minute,
            "burst_size": self.settings.rate_limit_per_minute * 2,
            "enabled": True
        }
    
    def export_config_summary(self) -> Dict[str, Any]:
        """Export configuration summary for debugging."""
        return {
            "app_info": {
                "name": self.settings.app_name,
                "version": self.settings.version,
                "debug": self.settings.debug,
                "log_level": self.settings.log_level
            },
            "database": {
                "type": "SQLite" if "sqlite" in self.settings.database_url else "Other",
                "url_masked": self.settings.database_url.replace(
                    self.settings.database_url.split("///")[-1], "***"
                ) if "///" in self.settings.database_url else "***"
            },
            "providers": {
                "available": self.get_available_providers(),
                "total_configured": len(self.get_available_providers())
            },
            "features": {
                "websocket_enabled": True,
                "chart_generation": True,
                "mcp_servers": True,
                "conversation_management": True
            },
            "security": {
                "cors_origins_count": len(self.settings.cors_origins),
                "rate_limiting": self.settings.rate_limit_per_minute > 0
            }
        }
    
    def validate_runtime_config(self) -> Dict[str, Any]:
        """Validate runtime configuration and return status."""
        issues = []
        warnings = []
        
        # Check API keys
        if not self.get_available_providers():
            issues.append("No LLM provider API keys configured")
        
        # Check database accessibility
        try:
            from app.config.database import engine
            with engine.connect():
                pass
        except Exception as e:
            issues.append(f"Database connection failed: {str(e)}")
        
        # Check static files
        static_path = Path("app/static")
        if not static_path.exists():
            warnings.append("Static files directory not found")
        
        # Check templates
        templates_path = Path("app/templates")
        if not templates_path.exists():
            warnings.append("Templates directory not found")
        
        return {
            "status": "healthy" if not issues else "unhealthy",
            "issues": issues,
            "warnings": warnings,
            "timestamp": os.environ.get("DEPLOYMENT_TIME", "unknown")
        }


# Global configuration manager instance
config_manager = ConfigurationManager()