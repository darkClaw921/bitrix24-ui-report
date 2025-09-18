"""Base LLM provider abstract class with LangChain integration."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from pydantic import BaseModel


class StreamingCallback(BaseCallbackHandler):
    """Callback handler for streaming responses."""
    
    def __init__(self):
        self.content = ""
        self.tokens = []
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token."""
        self.tokens.append(token)
        self.content += token


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config
        self.provider_name = self.get_provider_name()
        self.supported_models = self.get_supported_models()
        self.default_model = self.get_default_model()
        self._validate_config()
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of supported models."""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model name."""
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider configuration."""
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate response from messages."""
        pass
    
    @abstractmethod
    async def stream_response(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from messages."""
        pass
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model = model_name or self.default_model
        
        return {
            "provider": self.provider_name,
            "model": model,
            "supported": model in self.supported_models,
            "max_tokens": self.config.get("max_tokens", 1000),
            "temperature_range": (0.0, 2.0),
        }
    
    def is_model_supported(self, model_name: str) -> bool:
        """Check if a model is supported by this provider."""
        return model_name in self.supported_models
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the provider."""
        try:
            # Simple test message
            test_messages = [HumanMessage(content="Hello")]
            await self.generate_response(test_messages, max_tokens=10)
            return {
                "status": "healthy",
                "provider": self.provider_name,
                "message": "Provider is responding correctly"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_name,
                "error": str(e)
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the provider API."""
        # This is a default implementation that can be overridden by specific providers
        try:
            # Simple test message
            test_messages = [HumanMessage(content="Hello")]
            await self.generate_response(test_messages, max_tokens=10)
            return {
                "status": "connected",
                "message": f"Successfully connected to {self.provider_name} API",
                "provider": self.provider_name
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "provider": self.provider_name
            }


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class ConfigurationError(ProviderError):
    """Configuration validation error."""
    pass


class ModelNotSupportedError(ProviderError):
    """Model not supported error."""
    pass


class ProviderUnavailableError(ProviderError):
    """Provider unavailable error."""
    pass