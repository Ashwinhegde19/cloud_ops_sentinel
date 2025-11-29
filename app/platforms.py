"""
Platform management module for Cloud Ops Sentinel
Handles cloud platform connections with encrypted credential storage.
"""

import os
import json
from datetime import datetime
from typing import List, Optional, Dict
from cryptography.fernet import Fernet

from .database import get_db_session, PlatformDB
from .models import Platform, PlatformConfig, ConnectionResult


# Encryption key - in production, use a secure key management system
def _get_encryption_key() -> bytes:
    """Get or generate encryption key."""
    key = os.getenv("ENCRYPTION_KEY")
    if key:
        return key.encode()
    
    # Generate a key if not set (for development)
    # In production, this should be set via environment variable
    key_file = ".encryption_key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        new_key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(new_key)
        return new_key


_fernet = None


def _get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_encryption_key())
    return _fernet


def encrypt_credentials(credentials: Dict[str, str]) -> str:
    """
    Encrypt credentials dictionary for secure storage.
    
    Args:
        credentials: Dictionary of credential key-value pairs
    
    Returns:
        Encrypted string
    """
    json_str = json.dumps(credentials)
    encrypted = _get_fernet().encrypt(json_str.encode())
    return encrypted.decode()


def decrypt_credentials(encrypted: str) -> Dict[str, str]:
    """
    Decrypt credentials from storage.
    
    Args:
        encrypted: Encrypted credentials string
    
    Returns:
        Dictionary of credential key-value pairs
    """
    decrypted = _get_fernet().decrypt(encrypted.encode())
    return json.loads(decrypted.decode())


def list_platforms() -> List[Platform]:
    """
    Get all configured platforms.
    
    Returns:
        List of Platform objects (credentials remain encrypted)
    """
    db = get_db_session()
    try:
        platforms = db.query(PlatformDB).filter(PlatformDB.is_active == True).all()
        return [
            Platform(
                id=p.id,
                name=p.name,
                type=p.type,
                encrypted_credentials=p.encrypted_credentials,
                is_active=p.is_active,
                last_tested=p.last_tested,
                connection_status=p.connection_status,
                created_at=p.created_at
            )
            for p in platforms
        ]
    finally:
        db.close()


def get_platform(platform_id: str) -> Optional[Platform]:
    """Get a platform by ID."""
    db = get_db_session()
    try:
        p = db.query(PlatformDB).filter(PlatformDB.id == platform_id).first()
        if not p:
            return None
        
        return Platform(
            id=p.id,
            name=p.name,
            type=p.type,
            encrypted_credentials=p.encrypted_credentials,
            is_active=p.is_active,
            last_tested=p.last_tested,
            connection_status=p.connection_status,
            created_at=p.created_at
        )
    finally:
        db.close()


def add_platform(config: PlatformConfig, created_by: str = None) -> Platform:
    """
    Add a new platform connection.
    
    Args:
        config: Platform configuration with credentials
        created_by: User ID who created the platform
    
    Returns:
        Created Platform object
    """
    db = get_db_session()
    try:
        # Encrypt credentials
        encrypted = encrypt_credentials(config.credentials)
        
        # Create platform
        platform_db = PlatformDB(
            name=config.name,
            type=config.type,
            encrypted_credentials=encrypted,
            is_active=True,
            connection_status="unknown",
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        db.add(platform_db)
        db.commit()
        db.refresh(platform_db)
        
        return Platform(
            id=platform_db.id,
            name=platform_db.name,
            type=platform_db.type,
            encrypted_credentials=platform_db.encrypted_credentials,
            is_active=platform_db.is_active,
            last_tested=platform_db.last_tested,
            connection_status=platform_db.connection_status,
            created_at=platform_db.created_at
        )
    finally:
        db.close()


def update_platform(platform_id: str, config: PlatformConfig) -> Optional[Platform]:
    """
    Update an existing platform.
    
    Args:
        platform_id: ID of platform to update
        config: New configuration
    
    Returns:
        Updated Platform or None if not found
    """
    db = get_db_session()
    try:
        platform_db = db.query(PlatformDB).filter(PlatformDB.id == platform_id).first()
        if not platform_db:
            return None
        
        platform_db.name = config.name
        platform_db.type = config.type
        platform_db.encrypted_credentials = encrypt_credentials(config.credentials)
        platform_db.connection_status = "unknown"  # Reset status after update
        
        db.commit()
        db.refresh(platform_db)
        
        return Platform(
            id=platform_db.id,
            name=platform_db.name,
            type=platform_db.type,
            encrypted_credentials=platform_db.encrypted_credentials,
            is_active=platform_db.is_active,
            last_tested=platform_db.last_tested,
            connection_status=platform_db.connection_status,
            created_at=platform_db.created_at
        )
    finally:
        db.close()


def delete_platform(platform_id: str) -> bool:
    """
    Delete a platform and its credentials.
    
    Args:
        platform_id: ID of platform to delete
    
    Returns:
        True if deleted, False if not found
    """
    db = get_db_session()
    try:
        platform_db = db.query(PlatformDB).filter(PlatformDB.id == platform_id).first()
        if not platform_db:
            return False
        
        db.delete(platform_db)
        db.commit()
        return True
    finally:
        db.close()


def test_connection(platform_id: str) -> ConnectionResult:
    """
    Test connectivity to a platform.
    
    Args:
        platform_id: ID of platform to test
    
    Returns:
        ConnectionResult with success status and message
    """
    db = get_db_session()
    try:
        platform_db = db.query(PlatformDB).filter(PlatformDB.id == platform_id).first()
        if not platform_db:
            return ConnectionResult(
                platform_id=platform_id,
                success=False,
                message="Platform not found",
                tested_at=datetime.utcnow()
            )
        
        # Decrypt credentials
        try:
            credentials = decrypt_credentials(platform_db.encrypted_credentials)
        except Exception as e:
            return ConnectionResult(
                platform_id=platform_id,
                success=False,
                message=f"Failed to decrypt credentials: {str(e)}",
                tested_at=datetime.utcnow()
            )
        
        # Test based on platform type
        success, message, latency = _test_platform_connection(platform_db.type, credentials)
        
        # Update platform status
        platform_db.last_tested = datetime.utcnow()
        platform_db.connection_status = "connected" if success else "failed"
        db.commit()
        
        return ConnectionResult(
            platform_id=platform_id,
            success=success,
            message=message,
            latency_ms=latency,
            tested_at=datetime.utcnow()
        )
    finally:
        db.close()


def _test_platform_connection(platform_type: str, credentials: Dict) -> tuple:
    """
    Test connection to a specific platform type.
    
    Returns:
        Tuple of (success, message, latency_ms)
    """
    import time
    start = time.time()
    
    try:
        if platform_type == "aws":
            return _test_aws_connection(credentials)
        elif platform_type == "gcp":
            return _test_gcp_connection(credentials)
        elif platform_type == "azure":
            return _test_azure_connection(credentials)
        elif platform_type == "custom":
            return _test_custom_connection(credentials)
        else:
            return False, f"Unknown platform type: {platform_type}", None
    except Exception as e:
        latency = (time.time() - start) * 1000
        return False, f"Connection error: {str(e)}", latency


def _test_aws_connection(credentials: Dict) -> tuple:
    """Test AWS connection (simulated for hackathon)."""
    import time
    start = time.time()
    
    # Check required credentials
    if not credentials.get("access_key") or not credentials.get("secret_key"):
        return False, "Missing AWS credentials (access_key, secret_key)", None
    
    # Simulate connection test
    time.sleep(0.1)  # Simulate network latency
    latency = (time.time() - start) * 1000
    
    # For hackathon, simulate success if credentials are provided
    return True, "AWS connection successful", latency


def _test_gcp_connection(credentials: Dict) -> tuple:
    """Test GCP connection (simulated for hackathon)."""
    import time
    start = time.time()
    
    if not credentials.get("service_account_json") or not credentials.get("project_id"):
        return False, "Missing GCP credentials (service_account_json, project_id)", None
    
    time.sleep(0.1)
    latency = (time.time() - start) * 1000
    return True, "GCP connection successful", latency


def _test_azure_connection(credentials: Dict) -> tuple:
    """Test Azure connection (simulated for hackathon)."""
    import time
    start = time.time()
    
    required = ["tenant_id", "client_id", "client_secret", "subscription_id"]
    missing = [k for k in required if not credentials.get(k)]
    if missing:
        return False, f"Missing Azure credentials: {', '.join(missing)}", None
    
    time.sleep(0.1)
    latency = (time.time() - start) * 1000
    return True, "Azure connection successful", latency


def _test_custom_connection(credentials: Dict) -> tuple:
    """Test custom platform connection."""
    import time
    import requests
    start = time.time()
    
    endpoint = credentials.get("api_endpoint")
    api_key = credentials.get("api_key")
    
    if not endpoint:
        return False, "Missing api_endpoint", None
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        response = requests.get(endpoint, headers=headers, timeout=5)
        latency = (time.time() - start) * 1000
        
        if response.status_code < 400:
            return True, f"Connection successful (HTTP {response.status_code})", latency
        else:
            return False, f"Connection failed (HTTP {response.status_code})", latency
    except requests.exceptions.Timeout:
        return False, "Connection timeout", None
    except Exception as e:
        latency = (time.time() - start) * 1000
        return False, f"Connection error: {str(e)}", latency


# Platform type configurations
PLATFORM_TYPES = {
    "aws": {
        "name": "Amazon Web Services",
        "fields": ["access_key", "secret_key", "region"],
        "required": ["access_key", "secret_key"]
    },
    "gcp": {
        "name": "Google Cloud Platform",
        "fields": ["service_account_json", "project_id"],
        "required": ["service_account_json", "project_id"]
    },
    "azure": {
        "name": "Microsoft Azure",
        "fields": ["tenant_id", "client_id", "client_secret", "subscription_id"],
        "required": ["tenant_id", "client_id", "client_secret", "subscription_id"]
    },
    "custom": {
        "name": "Custom Platform",
        "fields": ["api_endpoint", "api_key"],
        "required": ["api_endpoint"]
    }
}


def get_platform_types() -> Dict:
    """Get available platform types and their configurations."""
    return PLATFORM_TYPES
