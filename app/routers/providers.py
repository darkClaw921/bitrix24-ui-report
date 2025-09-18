"""Provider configuration API router."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.config.database import get_database
from app.models.provider_config import ProviderConfig as ProviderConfigModel
from app.schemas.chat import ProviderConfigRequest
from app.services.llm_manager import llm_manager

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/")
async def get_all_providers():
    """Get information about all LLM providers."""
    return llm_manager.get_all_providers_info()


@router.get("/{provider_name}/config")
async def get_provider_config(provider_name: str, db: Session = Depends(get_database)):
    """Get configuration for a specific LLM provider."""
    try:
        # Check if provider exists in database
        config = db.query(ProviderConfigModel).filter(
            ProviderConfigModel.provider_name == provider_name,
            ProviderConfigModel.is_active == True
        ).first()
        
        if config:
            return {
                "provider_name": config.provider_name,
                "default_model": config.default_model,
                "is_configured": True
            }
        else:
            return {
                "provider_name": provider_name,
                "is_configured": False,
                "message": "Provider not configured"
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provider configuration: {str(e)}"
        )


@router.post("/{provider_name}/config")
async def save_provider_config(
    provider_name: str,
    config_data: ProviderConfigRequest,
    db: Session = Depends(get_database)
):
    """Save configuration for a specific LLM provider."""
    try:
        # Validate provider name
        supported_providers = ["openai", "grok", "anthropic"]
        if provider_name not in supported_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider_name}"
            )
        
        # Check if config already exists
        existing_config = db.query(ProviderConfigModel).filter(
            ProviderConfigModel.provider_name == provider_name
        ).first()
        
        if existing_config:
            # Update existing config
            existing_config.api_key = config_data.api_key
            existing_config.default_model = config_data.default_model
            existing_config.is_active = True
            existing_config.updated_at = ProviderConfigModel.__table__.c.updated_at.default.arg
        else:
            # Create new config
            existing_config = ProviderConfigModel(
                provider_name=provider_name,
                api_key=config_data.api_key,
                default_model=config_data.default_model,
                is_active=True
            )
            db.add(existing_config)
        
        db.commit()
        db.refresh(existing_config)
        
        return {
            "message": "Provider configuration saved successfully",
            "provider_name": provider_name,
            "config": existing_config.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save provider configuration: {str(e)}"
        )


@router.post("/{provider_name}/test")
async def test_provider_connection(
    provider_name: str,
    config_data: ProviderConfigRequest,
    db: Session = Depends(get_database)
):
    """Test connection to a specific LLM provider."""
    try:
        # Validate provider name
        supported_providers = ["openai", "grok", "anthropic"]
        if provider_name not in supported_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider_name}"
            )
        
        # Test the provider connection
        test_result = await llm_manager.test_provider_connection(
            provider_name, 
            config_data.api_key, 
            config_data.default_model
        )
        
        return test_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test provider connection: {str(e)}"
        )


@router.delete("/{provider_name}/config")
async def delete_provider_config(provider_name: str, db: Session = Depends(get_database)):
    """Delete configuration for a specific LLM provider."""
    try:
        # Validate provider name
        supported_providers = ["openai", "grok", "anthropic"]
        if provider_name not in supported_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider_name}"
            )
        
        # Find and delete the config
        config = db.query(ProviderConfigModel).filter(
            ProviderConfigModel.provider_name == provider_name
        ).first()
        
        if config:
            db.delete(config)
            db.commit()
            return {"message": f"Configuration for {provider_name} deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration for {provider_name} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete provider configuration: {str(e)}"
        )