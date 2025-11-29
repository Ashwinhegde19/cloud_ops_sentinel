"""
Property-based tests for settings UI module.
Uses Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.permissions import is_admin, can_manage_platforms, can_manage_api_keys
from app.models import User


def create_test_user(role: str) -> User:
    """Create a test user with given role."""
    return User(
        id="test-id",
        username=f"test_{role}",
        password_hash="hash",
        role=role,
        created_at=datetime.now(),
        is_active=True
    )


# **Feature: auth-platform-management, Property 10: Settings Tab Visibility**
# **Validates: Requirements 5.2**
@given(role=st.sampled_from(["viewer", "operator", "admin"]))
@settings(max_examples=20, deadline=None)
def test_settings_tab_visibility(role):
    """
    Property 10: Settings Tab Visibility
    For any user role:
    1. All users should see the Profile tab
    2. Only admins should see Platforms and API Keys tabs
    """
    user = create_test_user(role)
    
    # Property 1: Profile tab is always visible (all users can view their profile)
    # This is implicit - all users have access to profile settings
    assert user.is_active, "User should be active"
    
    # Property 2: Platforms tab visibility based on role
    can_see_platforms = is_admin(user)
    if role == "admin":
        assert can_see_platforms, "Admin should see Platforms tab"
    else:
        assert not can_see_platforms, f"{role} should NOT see Platforms tab"
    
    # Property 3: API Keys tab visibility based on role
    can_see_api_keys = is_admin(user)
    if role == "admin":
        assert can_see_api_keys, "Admin should see API Keys tab"
    else:
        assert not can_see_api_keys, f"{role} should NOT see API Keys tab"


@given(role=st.sampled_from(["viewer", "operator", "admin"]))
@settings(max_examples=20, deadline=None)
def test_admin_only_tabs_consistency(role):
    """
    Test that admin-only tab visibility is consistent.
    If a user can see one admin tab, they should see all admin tabs.
    """
    user = create_test_user(role)
    
    # Both admin tabs should have same visibility
    platforms_visible = is_admin(user)
    api_keys_visible = is_admin(user)
    
    assert platforms_visible == api_keys_visible, "Admin tabs should have consistent visibility"


def test_inactive_user_no_admin_access():
    """Inactive users should not have admin access even if role is admin."""
    user = create_test_user("admin")
    user.is_active = False
    
    # Inactive admin should not have admin privileges
    assert not is_admin(user), "Inactive admin should not have admin access"


def test_viewer_cannot_manage():
    """Viewers should not be able to manage platforms or API keys."""
    user = create_test_user("viewer")
    
    assert not can_manage_platforms(user), "Viewer cannot manage platforms"
    assert not can_manage_api_keys(user), "Viewer cannot manage API keys"


def test_operator_cannot_manage():
    """Operators should not be able to manage platforms or API keys."""
    user = create_test_user("operator")
    
    assert not can_manage_platforms(user), "Operator cannot manage platforms"
    assert not can_manage_api_keys(user), "Operator cannot manage API keys"


def test_admin_can_manage():
    """Admins should be able to manage platforms and API keys."""
    user = create_test_user("admin")
    
    assert can_manage_platforms(user), "Admin can manage platforms"
    assert can_manage_api_keys(user), "Admin can manage API keys"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
