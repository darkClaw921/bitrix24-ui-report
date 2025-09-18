"""Grok provider implementation with LangChain integration."""

from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import BaseMessage
from app.providers.base import BaseLLMProvider, ConfigurationError, ModelNotSupportedError, ProviderUnavailableError
import httpx


class GrokProvider(BaseLLMProvider):
    """Grok provider implementation using LangChain with OpenAI-compatible API."""
    
    SUPPORTED_MODELS = [
        "grok-beta",
        "grok-v1",
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Grok provider."""
        super().__init__(config)
        self._initialize_client()
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "grok"
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported models."""
        return self.SUPPORTED_MODELS
    
    def get_default_model(self) -> str:
        """Get the default model name."""
        return self.config.get("default_model", "grok-beta")
    
    def _validate_config(self) -> None:
        """Validate Grok configuration."""
        if not self.config.get("api_key"):
            raise ConfigurationError("Grok API key is required")
        
        default_model = self.get_default_model()
        if default_model not in self.SUPPORTED_MODELS:
            raise ConfigurationError(f"Default model {default_model} is not supported")
        
        # Validate base URL
        base_url = self.config.get("base_url", "https://api.x.ai/v1")
        if not base_url.startswith(("http://", "https://")):
            raise ConfigurationError("Invalid base URL format")
    
    def _initialize_client(self) -> None:
        """Initialize Grok client."""
        try:
            self.base_url = self.config.get("base_url", "https://api.x.ai/v1")
            self.base_params = {
                "openai_api_key": self.config["api_key"],
                "openai_api_base": self.base_url,
                "temperature": self.config.get("temperature", 0.7),
                "max_tokens": self.config.get("max_tokens", 1000),
            }
                
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Grok client: {str(e)}")
    
    async def generate_response(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate response from messages."""
        try:
            model_name = model or self.default_model
            
            if not self.is_model_supported(model_name):
                raise ModelNotSupportedError(f"Model {model_name} is not supported by Grok provider")
            
            # Create ChatOpenAI instance with Grok endpoint
            llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                **self.base_params
            )
            
            # Generate response
            response = await llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            if "api key" in str(e).lower() or "unauthorized" in str(e).lower():
                raise ConfigurationError(f"Grok API key error: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise ProviderUnavailableError(f"Grok rate limit exceeded: {str(e)}")
            else:
                raise ProviderUnavailableError(f"Grok provider error: {str(e)}")
    
    async def stream_response(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from messages."""
        try:
            model_name = model or self.default_model
            
            if not self.is_model_supported(model_name):
                raise ModelNotSupportedError(f"Model {model_name} is not supported by Grok provider")
            
            # Create ChatOpenAI instance for streaming
            llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=True,
                **self.base_params
            )
            
            # Stream response
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            if "api key" in str(e).lower() or "unauthorized" in str(e).lower():
                raise ConfigurationError(f"Grok API key error: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise ProviderUnavailableError(f"Grok rate limit exceeded: {str(e)}")
            else:
                raise ProviderUnavailableError(f"Grok provider error: {str(e)}")
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model = model_name or self.default_model
        base_info = super().get_model_info(model)
        
        # Add Grok-specific model information
        model_info = {
            **base_info,
            "context_window": self._get_context_window(model),
            "supports_functions": False,  # Grok doesn't support function calling yet
            "supports_streaming": True,
            "base_url": self.base_url
        }
        
        return model_info
    
    def _get_context_window(self, model: str) -> int:
        """Get context window size for model."""
        context_windows = {
            "grok-beta": 32768,
            "grok-v1": 32768,
        }
        return context_windows.get(model, 32768)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Grok API."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                # Test with a simple request
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": self.default_model,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 5
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {
                        "status": "connected",
                        "message": "Successfully connected to Grok API",
                        "model": self.default_model
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Connection failed with status {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}"
            }