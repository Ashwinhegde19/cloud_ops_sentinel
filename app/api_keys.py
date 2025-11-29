"""
API Key management module for Cloud Ops Sentinel
Secure storage and retrieval of API keys for sponsor integrations.
"""

import os
from datetime import datetime
from typing import List, Optional

from .database import get_db_session, ApiKeyDB
from .models import ApiKey, ApiKeyInfo
from .platforms import encrypt_credentials, decrypt_credentials


# Supported services
SUPPORTED_SERVICES = [
    "sambanova",
    "modal",
    "hyperbolic",
    "blaxel",
    "huggingface",
    "openai",
    "anthropic",
    "custom"
]


def mask_key(value: str) -> str:
    """
    Mask an API key for display, showing only last 4 characters.
    
    Args:
        value: Full API key value
    
    Returns:
        Masked string like "****xxxx"
    """
    if not value:
        return "****"
    
    if len(value) <= 4:
        return "*" * len(value)
    
    return "*" * (len(value) - 4) + value[-4:]


def list_keys() -> List[ApiKeyInfo]:
    """
    Get all API keys with masked values.
    
    Returns:
        List of ApiKeyInfo objects with masked values
    """
    db = get_db_session()
    try:
        keys = db.query(ApiKeyDB).all()
        result = []
        
        for k in keys:
            # Decrypt to get original value for masking
            try:
                decrypted = decrypt_credentials(k.encrypted_value)
                original_value = decrypted.get("value", "")
                masked = mask_key(original_value)
            except Exception:
                masked = "****[error]"
            
            result.append(ApiKeyInfo(
                id=k.id,
                name=k.name,
                service=k.service,
                masked_value=masked,
                created_at=k.created_at
            ))
        
        return result
    finally:
        db.close()


def add_key(name: str, value: str, service: str, created_by: str = None) -> ApiKey:
    """
    Add a new API key.
    
    Args:
        name: Display name for the key
        value: The actual API key value
        service: Service this key is for (sambanova, modal, etc.)
        created_by: User ID who created the key
    
    Returns:
        Created ApiKey object
    """
    db = get_db_session()
    try:
        # Encrypt the key value
        encrypted = encrypt_credentials({"value": value})
        
        key_db = ApiKeyDB(
            name=name,
            service=service,
            encrypted_value=encrypted,
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        db.add(key_db)
        db.commit()
        db.refresh(key_db)
        
        # Sync to environment variable immediately
        _sync_key_to_env(service, value)
        
        return ApiKey(
            id=key_db.id,
            name=key_db.name,
            service=key_db.service,
            encrypted_value=key_db.encrypted_value,
            created_at=key_db.created_at,
            last_used=key_db.last_used
        )
    finally:
        db.close()


def _sync_key_to_env(service: str, value: str):
    """Sync a single key to environment variable."""
    env_mapping = {
        "sambanova": "SAMBANOVA_API_KEY",
        "modal": "MODAL_TOKEN_ID",
        "hyperbolic": "HYPERBOLIC_API_KEY",
        "blaxel": "BLAXEL_API_KEY",
        "huggingface": "HF_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY"
    }
    env_var = env_mapping.get(service)
    if env_var and value:
        os.environ[env_var] = value


def update_key(key_id: str, value: str) -> Optional[ApiKey]:
    """
    Update an existing API key's value.
    
    Args:
        key_id: ID of key to update
        value: New API key value
    
    Returns:
        Updated ApiKey or None if not found
    """
    db = get_db_session()
    try:
        key_db = db.query(ApiKeyDB).filter(ApiKeyDB.id == key_id).first()
        if not key_db:
            return None
        
        # Encrypt new value
        key_db.encrypted_value = encrypt_credentials({"value": value})
        db.commit()
        db.refresh(key_db)
        
        # Sync to environment variable immediately
        _sync_key_to_env(key_db.service, value)
        
        return ApiKey(
            id=key_db.id,
            name=key_db.name,
            service=key_db.service,
            encrypted_value=key_db.encrypted_value,
            created_at=key_db.created_at,
            last_used=key_db.last_used
        )
    finally:
        db.close()


def delete_key(key_id: str) -> bool:
    """
    Delete an API key.
    
    Args:
        key_id: ID of key to delete
    
    Returns:
        True if deleted, False if not found
    """
    db = get_db_session()
    try:
        key_db = db.query(ApiKeyDB).filter(ApiKeyDB.id == key_id).first()
        if not key_db:
            return False
        
        service = key_db.service
        db.delete(key_db)
        db.commit()
        
        # Clear from environment variable
        _clear_key_from_env(service)
        
        return True
    finally:
        db.close()


def _clear_key_from_env(service: str):
    """Clear a key from environment variable."""
    env_mapping = {
        "sambanova": "SAMBANOVA_API_KEY",
        "modal": "MODAL_TOKEN_ID",
        "hyperbolic": "HYPERBOLIC_API_KEY",
        "blaxel": "BLAXEL_API_KEY",
        "huggingface": "HF_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY"
    }
    env_var = env_mapping.get(service)
    if env_var and env_var in os.environ:
        del os.environ[env_var]


def get_key(service: str) -> Optional[str]:
    """
    Get decrypted API key for a service.
    Updates last_used timestamp.
    
    Args:
        service: Service name (sambanova, modal, etc.)
    
    Returns:
        Decrypted API key value or None if not found
    """
    db = get_db_session()
    try:
        key_db = db.query(ApiKeyDB).filter(ApiKeyDB.service == service).first()
        if not key_db:
            return None
        
        # Update last used
        key_db.last_used = datetime.utcnow()
        db.commit()
        
        # Decrypt and return
        decrypted = decrypt_credentials(key_db.encrypted_value)
        return decrypted.get("value")
    except Exception:
        return None
    finally:
        db.close()


def get_key_info(key_id: str) -> Optional[ApiKeyInfo]:
    """Get API key info by ID."""
    db = get_db_session()
    try:
        key_db = db.query(ApiKeyDB).filter(ApiKeyDB.id == key_id).first()
        if not key_db:
            return None
        
        try:
            decrypted = decrypt_credentials(key_db.encrypted_value)
            masked = mask_key(decrypted.get("value", ""))
        except Exception:
            masked = "****[error]"
        
        return ApiKeyInfo(
            id=key_db.id,
            name=key_db.name,
            service=key_db.service,
            masked_value=masked,
            created_at=key_db.created_at
        )
    finally:
        db.close()


def sync_keys_to_env():
    """
    Sync stored API keys to environment variables.
    Call this on startup to make keys available to existing code.
    """
    db = get_db_session()
    try:
        keys = db.query(ApiKeyDB).all()
        
        env_mapping = {
            "sambanova": "SAMBANOVA_API_KEY",
            "modal": "MODAL_TOKEN_ID",
            "hyperbolic": "HYPERBOLIC_API_KEY",
            "blaxel": "BLAXEL_API_KEY",
            "huggingface": "HF_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY"
        }
        
        for key in keys:
            env_var = env_mapping.get(key.service)
            if env_var:
                try:
                    decrypted = decrypt_credentials(key.encrypted_value)
                    value = decrypted.get("value")
                    if value:
                        os.environ[env_var] = value
                except Exception:
                    pass
    finally:
        db.close()


def get_supported_services() -> List[str]:
    """Get list of supported services."""
    return SUPPORTED_SERVICES.copy()
