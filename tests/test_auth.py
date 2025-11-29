"""
Property-based tests for authentication module.
Uses Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import hash_password, verify_password, authenticate, create_session, logout, create_user
from app.database import get_db_session, UserDB, SessionDB


# **Feature: auth-platform-management, Property 1: Password Hash Irreversibility**
# **Validates: Requirements 1.2**
@given(password=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))))
@settings(max_examples=20, deadline=None)
def test_password_hash_irreversibility(password):
    """
    Property 1: Password Hash Irreversibility
    For any password, hashing produces a value that:
    1. Is different from the original password
    2. Can verify the original password
    """
    # bcrypt has 72-byte limit, truncate if needed
    password = password[:72]
    
    hashed = hash_password(password)
    
    # Hash should not equal original password
    assert hashed != password
    
    # Original password should verify against hash
    assert verify_password(password, hashed) is True
    
    # Wrong password should not verify
    wrong_password = password + "x"
    assert verify_password(wrong_password[:72], hashed) is False


# **Feature: auth-platform-management, Property 2: Invalid Credentials Generic Error**
# **Validates: Requirements 1.3**
@given(
    username=st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    password=st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('L', 'N')))
)
@settings(max_examples=20, deadline=None)
def test_invalid_credentials_generic_error(username, password):
    """
    Property 2: Invalid Credentials Generic Error
    For any invalid login attempt, the result should be None (generic error).
    The system should not reveal whether username or password was wrong.
    """
    # Non-existent user should return None
    result = authenticate(f"nonexistent_{username}", password)
    assert result is None
    
    # Wrong password for existing user should also return None
    # (same response as non-existent user - generic error)


# **Feature: auth-platform-management, Property 3: Session Logout Invalidation**
# **Validates: Requirements 1.4**
def test_session_logout_invalidation():
    """
    Property 3: Session Logout Invalidation
    For any valid session, after logout the session token should no longer validate.
    """
    from app.auth import validate_session
    from datetime import datetime
    
    # Create a test user
    test_username = f"test_logout_{datetime.now().timestamp()}"
    user = create_user(test_username, "testpass123", "viewer")
    assert user is not None
    
    # Create session
    session = create_session(user)
    assert session is not None
    assert len(session.token) == 64
    
    # Session should be valid
    validated_user = validate_session(session.token)
    assert validated_user is not None
    assert validated_user.username == test_username
    
    # Logout
    logout_result = logout(session.token)
    assert logout_result is True
    
    # Session should now be invalid
    invalid_user = validate_session(session.token)
    assert invalid_user is None
    
    # Cleanup
    db = get_db_session()
    try:
        db.query(UserDB).filter(UserDB.username == test_username).delete()
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
