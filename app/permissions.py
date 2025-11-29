"""
Permissions module for Cloud Ops Sentinel
Role-based access control with hierarchical permissions.
"""

from functools import wraps
from typing import List, Callable, Optional

from .models import User


# Role hierarchy: admin > operator > viewer
ROLE_HIERARCHY = {
    "viewer": 1,
    "operator": 2,
    "admin": 3
}

# Permission definitions by role
ROLE_PERMISSIONS = {
    "viewer": [
        "read_dashboard",
        "read_reports",
        "read_metrics",
        "read_idle_instances",
        "read_anomalies",
        "read_forecast",
        "read_hygiene_score",
        "use_chat"
    ],
    "operator": [
        # Inherits all viewer permissions
        "restart_service",
        "run_remediation",
        "toggle_auto_remediation"
    ],
    "admin": [
        # Inherits all operator permissions
        "manage_users",
        "manage_platforms",
        "manage_api_keys",
        "view_settings",
        "edit_settings"
    ]
}


def get_role_level(role: str) -> int:
    """Get numeric level for a role."""
    return ROLE_HIERARCHY.get(role, 0)


def get_user_permissions(user: User) -> List[str]:
    """
    Get all permissions for a user based on their role.
    Includes inherited permissions from lower roles.
    
    Args:
        user: User to get permissions for
    
    Returns:
        List of permission strings
    """
    permissions = []
    user_level = get_role_level(user.role)
    
    for role, level in ROLE_HIERARCHY.items():
        if level <= user_level:
            permissions.extend(ROLE_PERMISSIONS.get(role, []))
    
    return list(set(permissions))  # Remove duplicates


def check_permission(user: User, permission: str) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user: User to check
        permission: Permission string to check
    
    Returns:
        True if user has permission, False otherwise
    """
    if not user or not user.is_active:
        return False
    
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def check_role(user: User, required_role: str) -> bool:
    """
    Check if a user has at least the required role level.
    
    Args:
        user: User to check
        required_role: Minimum required role
    
    Returns:
        True if user has sufficient role, False otherwise
    """
    if not user or not user.is_active:
        return False
    
    user_level = get_role_level(user.role)
    required_level = get_role_level(required_role)
    
    return user_level >= required_level


def is_admin(user: User) -> bool:
    """Check if user is an admin."""
    return user and user.is_active and user.role == "admin"


def is_operator_or_above(user: User) -> bool:
    """Check if user is operator or admin."""
    return check_role(user, "operator")


def require_role(required_role: str):
    """
    Decorator to require a minimum role for a function.
    
    Usage:
        @require_role("admin")
        def admin_only_function(user, ...):
            ...
    
    Args:
        required_role: Minimum required role
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(user: User, *args, **kwargs):
            if not check_role(user, required_role):
                raise PermissionError(f"Access denied. Required role: {required_role}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """
    Decorator to require a specific permission for a function.
    
    Usage:
        @require_permission("manage_users")
        def manage_users_function(user, ...):
            ...
    
    Args:
        permission: Required permission string
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(user: User, *args, **kwargs):
            if not check_permission(user, permission):
                raise PermissionError(f"Access denied. Required permission: {permission}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator


# Permission check functions for specific actions
def can_restart_service(user: User) -> bool:
    """Check if user can restart services."""
    return check_permission(user, "restart_service")


def can_manage_users(user: User) -> bool:
    """Check if user can manage users."""
    return check_permission(user, "manage_users")


def can_manage_platforms(user: User) -> bool:
    """Check if user can manage platforms."""
    return check_permission(user, "manage_platforms")


def can_manage_api_keys(user: User) -> bool:
    """Check if user can manage API keys."""
    return check_permission(user, "manage_api_keys")


def can_toggle_remediation(user: User) -> bool:
    """Check if user can toggle auto-remediation."""
    return check_permission(user, "toggle_auto_remediation")


def get_visible_tabs(user: User) -> List[str]:
    """
    Get list of UI tabs visible to user based on role.
    
    Args:
        user: User to check
    
    Returns:
        List of tab IDs that should be visible
    """
    tabs = [
        "dashboard",
        "idle",
        "cost",
        "metrics",
        "report",
        "chat",
        "hygiene"
    ]
    
    # Operator+ can see service control and remediation
    if is_operator_or_above(user):
        tabs.extend(["control", "remediation"])
    
    # Admin can see settings
    if is_admin(user):
        tabs.append("settings")
    
    return tabs
