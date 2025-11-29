"""
Property-based tests for API key management module.
Uses Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api_keys import (
    mask_key, add_key, get_key, delete_key, list_keys,
    SUPPORTED_SERVICES
)
from app.database import get_db_session, ApiKeyDB


# **Feature: auth-platform-management, Property 8: API Key Masking**
# **Validates: Requirements 4.1**
@given(
    key_value=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N')))
)
@settings(max_examples=50, deadline=None)
def test_api_key_masking(key_value):
    """
    Property 8: API Key Masking
    For any API key value, masking should:
    1. Show only the last 4 characters
    2. Replace all other characters with asterisks
    3. Never expose more than 4 characters
    """
    masked = mask_key(key_value)
    
    if len(key_value) <= 4:
        # Property 1: Short keys should be fully masked
        assert masked == "*" * len(key_value), "Short keys should be fully masked"
        assert key_value not in masked or len(key_value) == 0, "Short key should not be visible"
    else:
        # Property 2: Only last 4 chars should be visible
        assert masked.endswith(key_value[-4:]), "Last 4 chars should be visible"
        
        # Property 3: Rest should be asterisks
        asterisk_part = masked[:-4]
        assert all(c == '*' for c in asterisk_part), "Non-visible part should be asterisks"
        
        # Property 4: Length should match original
        assert len(masked) == len(key_value), "Masked length should match original"
        
        # Property 5: Full key should not be exposed
        if len(key_value) > 4:
            assert key_value not in masked, "Full key should not be exposed"


# **Feature: auth-platform-management, Property 9: API Key Encryption Round-Trip**
# **Validates: Requirements 4.2, 4.5**
@given(
    name=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    key_value=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    service=st.sampled_from(SUPPORTED_SERVICES)
)
@settings(max_examples=10, deadline=None)
def test_api_key_encryption_round_trip(name, key_value, service):
    """
    Property 9: API Key Encryption Round-Trip
    For any API key, storing then retrieving should return the original value.
    """
    # Create unique name to avoid conflicts
    unique_name = f"test_{name}_{datetime.now().timestamp()}"
    
    # Add key
    api_key = add_key(unique_name, key_value, service, created_by="test-user")
    assert api_key is not None, "Key should be created"
    
    try:
        # Property 1: Encrypted value should not contain plaintext
        assert key_value not in api_key.encrypted_value, "Encrypted should not contain plaintext"
        
        # Property 2: Retrieved key should match original (round-trip)
        retrieved = get_key(service)
        assert retrieved == key_value, "Retrieved key should match original"
        
        # Property 3: Key should appear in list (masked)
        keys = list_keys()
        test_key = next((k for k in keys if k.id == api_key.id), None)
        assert test_key is not None, "Key should appear in list"
        
        # Property 4: Listed key should be masked
        assert test_key.masked_value.endswith(key_value[-4:]), "Listed key should show last 4 chars"
        assert key_value not in test_key.masked_value, "Listed key should not expose full value"
        
    finally:
        # Cleanup
        delete_key(api_key.id)


def test_mask_key_empty():
    """Test masking empty key."""
    assert mask_key("") == "****"
    assert mask_key(None) == "****"


def test_mask_key_short():
    """Test masking short keys."""
    assert mask_key("a") == "*"
    assert mask_key("ab") == "**"
    assert mask_key("abc") == "***"
    assert mask_key("abcd") == "****"


def test_mask_key_standard():
    """Test masking standard length keys."""
    # "sk-12345678" is 11 chars, so 7 asterisks + last 4
    assert mask_key("sk-12345678") == "*******5678"
    # "FAKE_TEST_KEY_VALUE1" is 20 chars, so 16 asterisks + last 4 (LUE1)
    assert mask_key("FAKE_TEST_KEY_VALUE1") == "****************LUE1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
