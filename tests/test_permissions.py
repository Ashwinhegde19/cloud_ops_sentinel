"""
Property-based tests for permissions module.
Uses Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.permissions import (
    get_user_permissions, check_permission, check_role,
    is_admin, ROLE_HIERARCHY, ROLE_PERMISSIONS
)
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


# **Feature: auth-platform-management, Property 4: Role Permission Hierarchy**
# **Validates: Requirements 2.1, 2.2, 2.3**
@given(role=st.sampled_from(["viewer", "operator", "admin"]))
@settings(max_examples=20, deadline=None)
def test_role_permission_hierarchy(role):
    """
    Property 4: Role Permission Hierarchy
    For any user with role R, they should have all permissions of roles below them.
    admin > operator > viewer
    """
    user = create_test_user(role)
    user_perms = set(get_user_permissions(user))
    
    # Viewer permissions should always be included
    viewer_perms = set(ROLE_PERMISSIONS["viewer"])
    assert viewer_perms.issubset(user_perms), f"{role} should have all viewer permissions"
    
    # Operator permissions included for operator and admin
    if role in ["operator", "admin"]:
        operator_perms = set(ROLE_PERMISSIONS["operator"])
        assert operator_perms.issubset(user_perms), f"{role} should have all operator permissions"
    
    # Admin permissions only for admin
    if role == "admin":
        admin_perms = set(ROLE_PERMISSIONS["admin"])
        assert admin_perms.issubset(user_perms), "admin should have all admin permissions"


# **Feature: auth-platform-management, Property 5: Non-Admin Access Denial**
# **Validates: Requirements 2.4**
@given(role=st.sampled_from(["viewer", "operator"]))
@settings(max_examples=20, deadline=None)
def test_non_admin_access_denial(role):
    """
    Property 5: Non-Admin Access Denial
    For any user without admin role, admin-only permissions should be denied.
    """
    user = create_test_user(role)
    
    # Admin-only permissions
    admin_only_perms = ["manage_users", "manage_platforms", "manage_api_keys"]
    
    for perm in admin_only_perms:
        assert check_permission(user, perm) is False, f"{role} should not have {perm}"
    
    # is_admin should return False
    assert is_admin(user) is False


def test_admin_has_all_permissions():
    """Admin should have all permissions."""
    admin = create_test_user("admin")
    
    # Check all defined permissions
    all_perms = []
    for perms in ROLE_PERMISSIONS.values():
        all_perms.extend(perms)
    
    for perm in set(all_perms):
        assert check_permission(admin, perm) is True, f"admin should have {perm}"


def test_inactive_user_denied():
    """Inactive users should be denied all permissions."""
    user = create_test_user("admin")
    user.is_active = False
    
    assert check_permission(user, "read_dashboard") is False
    assert is_admin(user) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
