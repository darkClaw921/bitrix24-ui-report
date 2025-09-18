"""OpenAI provider implementation with LangChain integration."""

from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from app.providers.base import BaseLLMProvider, ConfigurationError, ModelNotSupportedError, ProviderUnavailableError
import asyncio
import httpx


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation using LangChain."""
    
    SUPPORTED_MODELS = [
        "gpt-4-turbo-preview",
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-1106",
        "gpt-4-1106-preview",
        "gpt-4-0125-preview"
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider."""
        super().__init__(config)
        self._initialize_client()
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported models."""
        return self.SUPPORTED_MODELS
    
    def get_default_model(self) -> str:
        """Get the default model name."""
        return self.config.get("default_model", "gpt-3.5-turbo")
    
    def _validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not self.config.get("api_key"):
            raise ConfigurationError("OpenAI API key is required")
        
        default_model = self.get_default_model()
        if default_model not in self.SUPPORTED_MODELS:
            raise ConfigurationError(f"Default model {default_model} is not supported")
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            self.base_params = {
                "openai_api_key": self.config["api_key"]
            }
            
            # Add optional parameters
            if self.config.get("organization"):
                self.base_params["openai_organization"] = self.config["organization"]
            
            if self.config.get("base_url"):
                self.base_params["openai_api_base"] = self.config["base_url"]
                
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize OpenAI client: {str(e)}")
    
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
                raise ModelNotSupportedError(f"Model {model_name} is not supported by OpenAI provider")
            
            # Create ChatOpenAI instance
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
            if "api key" in str(e).lower():
                raise ConfigurationError(f"OpenAI API key error: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise ProviderUnavailableError(f"OpenAI rate limit exceeded: {str(e)}")
            else:
                raise ProviderUnavailableError(f"OpenAI provider error: {str(e)}")
    
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
                raise ModelNotSupportedError(f"Model {model_name} is not supported by OpenAI provider")
            
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
            if "api key" in str(e).lower():
                raise ConfigurationError(f"OpenAI API key error: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise ProviderUnavailableError(f"OpenAI rate limit exceeded: {str(e)}")
            else:
                raise ProviderUnavailableError(f"OpenAI provider error: {str(e)}")
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model = model_name or self.default_model
        base_info = super().get_model_info(model)
        
        # Add OpenAI-specific model information
        model_info = {
            **base_info,
            "context_window": self._get_context_window(model),
            "supports_functions": self._supports_functions(model),
            "cost_per_1k_tokens": self._get_cost_info(model)
        }
        
        return model_info
    
    def _get_context_window(self, model: str) -> int:
        """Get context window size for model."""
        context_windows = {
            "gpt-4-turbo-preview": 128000,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-3.5-turbo-1106": 16384,
            "gpt-4-1106-preview": 128000,
            "gpt-4-0125-preview": 128000
        }
        return context_windows.get(model, 4096)
    
    def _supports_functions(self, model: str) -> bool:
        """Check if model supports function calling."""
        function_models = [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-1106",
            "gpt-4-1106-preview",
            "gpt-4-0125-preview"
        ]
        return model in function_models
    
    def _get_cost_info(self, model: str) -> Dict[str, float]:
        """Get cost information for model (approximate)."""
        costs = {
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
            "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
            "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
            "gpt-4-0125-preview": {"input": 0.01, "output": 0.03}
        }
        return costs.get(model, {"input": 0.001, "output": 0.002})
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to OpenAI API."""
        try:
            # Use httpx to test the connection directly
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                # Test with a simple request to the models endpoint
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {
                        "status": "connected",
                        "message": "Successfully connected to OpenAI API",
                        "provider": self.provider_name
                    }
                elif response.status_code == 401:
                    return {
                        "status": "error",
                        "message": "Invalid API key",
                        "provider": self.provider_name
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Connection failed with status {response.status_code}",
                        "provider": self.provider_name,
                        "details": response.text[:200]  # First 200 chars of response
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "provider": self.provider_name
            }