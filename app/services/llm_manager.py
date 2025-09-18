"""LLM manager service for handling multiple providers."""

from typing import Dict, List, Optional, Any, AsyncGenerator
from langchain.schema import BaseMessage
from app.providers.base import BaseLLMProvider, ProviderError
from app.providers.openai_provider import OpenAIProvider
from app.providers.grok_provider import GrokProvider
from app.config.settings import settings


class LLMManager:
    """Manager for multiple LLM providers."""
    
    def __init__(self):
        """Initialize LLM manager."""
        self.providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize all available providers."""
        # Initialize OpenAI provider if API key is available
        if settings.openai_api_key:
            try:
                openai_config = {
                    "api_key": settings.openai_api_key,
                    "default_model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                self.providers["openai"] = OpenAIProvider(openai_config)
            except Exception as e:
                print(f"Failed to initialize OpenAI provider: {e}")
        
        # Initialize Grok provider if API key is available
        if settings.grok_api_key:
            try:
                grok_config = {
                    "api_key": settings.grok_api_key,
                    "base_url": "https://api.x.ai/v1",
                    "default_model": "grok-beta",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                self.providers["grok"] = GrokProvider(grok_config)
            except Exception as e:
                print(f"Failed to initialize Grok provider: {e}")
    
    def get_provider(self, provider_name: str) -> Optional[BaseLLMProvider]:
        """Get a specific provider by name."""
        return self.providers.get(provider_name)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())
    
    def get_default_provider(self) -> Optional[BaseLLMProvider]:
        """Get the default provider."""
        if "openai" in self.providers:
            return self.providers["openai"]
        elif self.providers:
            return next(iter(self.providers.values()))
        return None
    
    def get_supported_models(self, provider_name: str) -> List[str]:
        """Get supported models for a provider."""
        provider = self.get_provider(provider_name)
        if provider:
            return provider.get_supported_models()
        return []
    
    def get_all_models(self) -> Dict[str, List[str]]:
        """Get all supported models for all providers."""
        return {
            provider_name: provider.get_supported_models()
            for provider_name, provider in self.providers.items()
        }
    
    async def generate_response(
        self,
        messages: List[BaseMessage],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate response using specified or default provider."""
        provider = self._get_provider_for_request(provider_name)
        if not provider:
            raise ProviderError(f"Provider '{provider_name}' is not available")
        
        return await provider.generate_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    async def stream_response(
        self,
        messages: List[BaseMessage],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response using specified or default provider."""
        provider = self._get_provider_for_request(provider_name)
        if not provider:
            raise ProviderError(f"Provider '{provider_name}' is not available")
        
        async for chunk in provider.stream_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        ):
            yield chunk
    
    def _get_provider_for_request(self, provider_name: Optional[str]) -> Optional[BaseLLMProvider]:
        """Get provider for request, fallback to default if not specified."""
        if provider_name:
            return self.get_provider(provider_name)
        return self.get_default_provider()
    
    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a specific provider."""
        provider = self.get_provider(provider_name)
        if not provider:
            return {"error": f"Provider '{provider_name}' not found"}
        
        return {
            "name": provider.provider_name,
            "supported_models": provider.get_supported_models(),
            "default_model": provider.get_default_model(),
            "available": True
        }
    
    def get_all_providers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available providers."""
        result = {}
        
        # Include all possible providers, even if not configured
        all_providers = ["openai", "grok", "anthropic"]
        
        for provider_name in all_providers:
            if provider_name in self.providers:
                # Provider is available
                provider = self.providers[provider_name]
                result[provider_name] = {
                    "name": provider_name,
                    "supported_models": provider.get_supported_models(),
                    "default_model": provider.get_default_model(),
                    "available": True,
                    "status": "configured"
                }
            else:
                # Provider is not configured
                result[provider_name] = {
                    "name": provider_name,
                    "supported_models": [],
                    "default_model": None,
                    "available": False,
                    "status": "not_configured"
                }
        
        return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers."""
        results = {}
        
        for provider_name, provider in self.providers.items():
            try:
                result = await provider.health_check()
                results[provider_name] = result
            except Exception as e:
                results[provider_name] = {
                    "status": "error",
                    "provider": provider_name,
                    "error": str(e)
                }
        
        return {
            "providers": results,
            "total_providers": len(self.providers),
            "healthy_providers": len([r for r in results.values() if r.get("status") == "healthy"])
        }
    
    async def test_provider_connection(self, provider_name: str, api_key: str, default_model: Optional[str] = None) -> Dict[str, Any]:
        """Test connection to a specific provider with provided credentials."""
        try:
            # Create temporary provider instance for testing
            if provider_name == "openai":
                from app.providers.openai_provider import OpenAIProvider
                config = {
                    "api_key": api_key,
                    "default_model": default_model or "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 10
                }
                provider = OpenAIProvider(config)
            elif provider_name == "grok":
                from app.providers.grok_provider import GrokProvider
                config = {
                    "api_key": api_key,
                    "base_url": "https://api.x.ai/v1",
                    "default_model": default_model or "grok-beta",
                    "temperature": 0.7,
                    "max_tokens": 10
                }
                provider = GrokProvider(config)
            elif provider_name == "anthropic":
                # For now, we'll create a basic config for testing
                config = {
                    "api_key": api_key,
                    "default_model": default_model or "claude-3-sonnet-20240229",
                    "temperature": 0.7,
                    "max_tokens": 10
                }
                # Since Anthropic provider is not implemented yet, we'll return a placeholder
                return {
                    "status": "not_implemented",
                    "provider": provider_name,
                    "message": "Anthropic provider not yet implemented"
                }
            else:
                return {
                    "status": "error",
                    "provider": provider_name,
                    "message": f"Unsupported provider: {provider_name}"
                }
            
            # Test the connection
            test_result = await provider.test_connection()
            return test_result
            
        except Exception as e:
            return {
                "status": "error",
                "provider": provider_name,
                "message": f"Connection test failed: {str(e)}"
            }
    
    def add_provider(self, provider_name: str, provider: BaseLLMProvider) -> None:
        """Add a new provider to the manager."""
        self.providers[provider_name] = provider
    
    def remove_provider(self, provider_name: str) -> bool:
        """Remove a provider from the manager."""
        if provider_name in self.providers:
            del self.providers[provider_name]
            return True
        return False
    
    def is_model_supported(self, provider_name: str, model_name: str) -> bool:
        """Check if a model is supported by a specific provider."""
        provider = self.get_provider(provider_name)
        if provider:
            return provider.is_model_supported(model_name)
        return False


# Global LLM manager instance
llm_manager = LLMManager()