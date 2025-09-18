"""Application settings and configuration."""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    app_name: str = "FastAPI LangChain Chatbot"
    debug: bool = False
    version: str = "0.1.0"
    
    # Database settings
    database_url: str = "sqlite:///./chatbot.db"
    
    # API Keys
    openai_api_key: Optional[str] = None
    grok_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # Logging
    log_level: str = "INFO"
    
    # Chart settings
    max_chart_data_points: int = 1000
    default_chart_type: str = "line"
    
    # WebSocket settings
    websocket_timeout: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow JSON parsing for list fields
        extra = "ignore"


# Global settings instance
settings = Settings()


class ProviderConfig:
    """Base provider configuration."""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        for key, value in kwargs.items():
            setattr(self, key, value)


class OpenAIConfig(ProviderConfig):
    """OpenAI provider configuration."""
    
    def __init__(
        self,
        api_key: str,
        organization: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        self.organization = organization
        self.base_url = base_url
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens


class GrokConfig(ProviderConfig):
    """Grok provider configuration."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.x.ai/v1",
        default_model: str = "grok-beta",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        self.base_url = base_url
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens


class AnthropicConfig(ProviderConfig):
    """Anthropic (Claude) provider configuration."""
    
    def __init__(
        self,
        api_key: str,
        default_model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens