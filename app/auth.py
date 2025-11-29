"""
Authentication module for Cloud Ops Sentinel
Handles user authentication, password hashing, and session management.
"""

import os
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from .database import get_db_session, UserDB, SessionDB
from .models import User, Session


# Session configuration
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored password hash
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def authenticate(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.
    Returns generic error for any invalid attempt (security best practice).
    
    Args:
        username: Username to authenticate
        password: Password to verify
    
    Returns:
        User object if authenticated, None otherwise
    """
    db = get_db_session()
    try:
        # Find user by username
        user_db = db.query(UserDB).filter(
            UserDB.username == username,
            UserDB.is_active == True
        ).first()
        
        if not user_db:
            # User not found - return None (generic error)
            return None
        
        # Verify password
        if not verify_password(password, user_db.password_hash):
            # Wrong password - return None (generic error)
            return None
        
        # Update last login
        user_db.last_login = datetime.utcnow()
        db.commit()
        
        # Return user model
        return User(
            id=user_db.id,
            username=user_db.username,
            password_hash=user_db.password_hash,
            role=user_db.role,
            email=user_db.email,
            created_at=user_db.created_at,
            last_login=user_db.last_login,
            is_active=user_db.is_active
        )
    finally:
        db.close()


def create_session(user: User) -> Session:
    """
    Create a new session for an authenticated user.
    
    Args:
        user: Authenticated user
    
    Returns:
        New session object
    """
    db = get_db_session()
    try:
        # Generate secure token
        token = secrets.token_hex(32)
        
        # Calculate expiry
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=SESSION_EXPIRY_HOURS)
        
        # Create session in database
        session_db = SessionDB(
            token=token,
            user_id=user.id,
            created_at=now,
            expires_at=expires_at,
            is_active=True
        )
        db.add(session_db)
        db.commit()
        
        return Session(
            token=token,
            user_id=user.id,
            created_at=now,
            expires_at=expires_at,
            is_active=True
        )
    finally:
        db.close()


def validate_session(token: str) -> Optional[User]:
    """
    Validate a session token and return the associated user.
    
    Args:
        token: Session token to validate
    
    Returns:
        User if session is valid, None otherwise
    """
    db = get_db_session()
    try:
        # Find session
        session_db = db.query(SessionDB).filter(
            SessionDB.token == token,
            SessionDB.is_active == True
        ).first()
        
        if not session_db:
            return None
        
        # Check expiry
        if datetime.utcnow() > session_db.expires_at:
            # Session expired - invalidate it
            session_db.is_active = False
            db.commit()
            return None
        
        # Get user
        user_db = db.query(UserDB).filter(
            UserDB.id == session_db.user_id,
            UserDB.is_active == True
        ).first()
        
        if not user_db:
            return None
        
        return User(
            id=user_db.id,
            username=user_db.username,
            password_hash=user_db.password_hash,
            role=user_db.role,
            email=user_db.email,
            created_at=user_db.created_at,
            last_login=user_db.last_login,
            is_active=user_db.is_active
        )
    finally:
        db.close()


def logout(token: str) -> bool:
    """
    Invalidate a session (logout).
    
    Args:
        token: Session token to invalidate
    
    Returns:
        True if session was invalidated, False if not found
    """
    db = get_db_session()
    try:
        session_db = db.query(SessionDB).filter(SessionDB.token == token).first()
        
        if not session_db:
            return False
        
        session_db.is_active = False
        db.commit()
        return True
    finally:
        db.close()


def create_user(username: str, password: str, role: str = "viewer", email: str = None) -> Optional[User]:
    """
    Create a new user.
    
    Args:
        username: Unique username
        password: Plain text password (will be hashed)
        role: User role (viewer, operator, admin)
        email: Optional email address
    
    Returns:
        Created user or None if username exists
    """
    db = get_db_session()
    try:
        # Check if username exists
        existing = db.query(UserDB).filter(UserDB.username == username).first()
        if existing:
            return None
        
        # Create user
        user_db = UserDB(
            username=username,
            password_hash=hash_password(password),
            role=role,
            email=email,
            created_at=datetime.utcnow(),
            is_active=True
        )
        db.add(user_db)
        db.commit()
        db.refresh(user_db)
        
        return User(
            id=user_db.id,
            username=user_db.username,
            password_hash=user_db.password_hash,
            role=user_db.role,
            email=user_db.email,
            created_at=user_db.created_at,
            last_login=None,
            is_active=True
        )
    finally:
        db.close()


def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID."""
    db = get_db_session()
    try:
        user_db = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user_db:
            return None
        
        return User(
            id=user_db.id,
            username=user_db.username,
            password_hash=user_db.password_hash,
            role=user_db.role,
            email=user_db.email,
            created_at=user_db.created_at,
            last_login=user_db.last_login,
            is_active=user_db.is_active
        )
    finally:
        db.close()


def update_user_password(user_id: str, new_password: str) -> bool:
    """Update user's password."""
    db = get_db_session()
    try:
        user_db = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user_db:
            return False
        
        user_db.password_hash = hash_password(new_password)
        db.commit()
        return True
    finally:
        db.close()


def list_users() -> list:
    """List all users (for admin)."""
    db = get_db_session()
    try:
        users = db.query(UserDB).all()
        return [
            User(
                id=u.id,
                username=u.username,
                password_hash="[hidden]",
                role=u.role,
                email=u.email,
                created_at=u.created_at,
                last_login=u.last_login,
                is_active=u.is_active
            )
            for u in users
        ]
    finally:
        db.close()


def ensure_admin_exists():
    """Ensure at least one admin user exists (for first run)."""
    db = get_db_session()
    try:
        admin = db.query(UserDB).filter(UserDB.role == "admin").first()
        if not admin:
            # Create default admin
            create_user(
                username="admin",
                password="admin123",  # Should be changed on first login
                role="admin",
                email="admin@cloudops.local"
            )
            print("Created default admin user (username: admin, password: admin123)")
    finally:
        db.close()
