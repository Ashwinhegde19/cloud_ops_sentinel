"""
Property-based tests for platform management module.
Uses Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.platforms import (
    encrypt_credentials, decrypt_credentials,
    add_platform, get_platform, delete_platform, list_platforms
)
from app.models import PlatformConfig
from app.database import get_db_session, PlatformDB


# **Feature: auth-platform-management, Property 6: Credential Encryption**
# **Validates: Requirements 3.3**
@given(
    key=st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    value=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))
)
@settings(max_examples=20, deadline=None)
def test_credential_encryption_round_trip(key, value):
    """
    Property 6: Credential Encryption Round-Trip
    For any credentials dictionary, encrypting then decrypting should return
    the original credentials.
    """
    credentials = {key: value}
    
    # Encrypt
    encrypted = encrypt_credentials(credentials)
    
    # Property 1: Encrypted should be different from original JSON
    assert encrypted != str(credentials), "Encrypted should differ from original"
    
    # Property 2: Decryption should return original (round-trip)
    decrypted = decrypt_credentials(encrypted)
    assert decrypted == credentials, "Decrypted should match original"
    
    # Property 3: Encrypted data should be base64-like (Fernet format)
    assert encrypted.startswith("gAAAAA"), "Should be Fernet encrypted format"


# **Feature: auth-platform-management, Property 7: Platform Deletion Cleanup**
# **Validates: Requirements 3.5**
@given(
    name=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    platform_type=st.sampled_from(["aws", "gcp", "azure", "custom"])
)
@settings(max_examples=10, deadline=None)
def test_platform_deletion_cleanup(name, platform_type):
    """
    Property 7: Platform Deletion Cleanup
    For any platform, after deletion:
    1. The platform should not be retrievable
    2. The credentials should be removed from storage
    """
    # Create test credentials based on platform type
    if platform_type == "aws":
        credentials = {"access_key": "test_key", "secret_key": "test_secret"}
    elif platform_type == "gcp":
        credentials = {"service_account_json": "{}", "project_id": "test-project"}
    elif platform_type == "azure":
        credentials = {
            "tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "subscription_id": "test-sub"
        }
    else:  # custom
        credentials = {"api_endpoint": "https://test.example.com", "api_key": "test"}
    
    # Create platform
    config = PlatformConfig(
        name=f"test_{name}_{datetime.now().timestamp()}",
        type=platform_type,
        credentials=credentials
    )
    
    platform = add_platform(config, created_by="test-user")
    assert platform is not None, "Platform should be created"
    platform_id = platform.id
    
    # Verify platform exists
    retrieved = get_platform(platform_id)
    assert retrieved is not None, "Platform should be retrievable"
    
    # Delete platform
    deleted = delete_platform(platform_id)
    assert deleted is True, "Deletion should succeed"
    
    # Property 1: Platform should not be retrievable after deletion
    after_delete = get_platform(platform_id)
    assert after_delete is None, "Platform should not exist after deletion"
    
    # Property 2: Verify not in database
    db = get_db_session()
    try:
        db_platform = db.query(PlatformDB).filter(PlatformDB.id == platform_id).first()
        assert db_platform is None, "Platform should be removed from database"
    finally:
        db.close()


def test_platform_credentials_not_exposed():
    """Test that platform list does not expose decrypted credentials."""
    # Create a test platform with fake test credentials
    config = PlatformConfig(
        name=f"test_exposure_{datetime.now().timestamp()}",
        type="aws",
        credentials={"access_key": "FAKE_TEST_ACCESS_KEY", "secret_key": "FAKE_TEST_SECRET_KEY"}
    )
    
    platform = add_platform(config, created_by="test-user")
    
    try:
        # List platforms
        platforms = list_platforms()
        
        # Find our test platform
        test_platform = next((p for p in platforms if p.id == platform.id), None)
        assert test_platform is not None
        
        # Credentials should be encrypted, not plaintext
        assert "FAKE_TEST_ACCESS_KEY" not in test_platform.encrypted_credentials
        assert "FAKE_TEST_SECRET_KEY" not in test_platform.encrypted_credentials
        
    finally:
        # Cleanup
        delete_platform(platform.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
