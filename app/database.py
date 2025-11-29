"""
Database module for Cloud Ops Sentinel
SQLite database with SQLAlchemy ORM for users, sessions, platforms, and API keys.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cloud_ops_sentinel.db")

# Create engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_uuid() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


# ============== DATABASE MODELS ==============

class UserDB(Base):
    """User database model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")  # viewer, operator, admin
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    sessions = relationship("SessionDB", back_populates="user", cascade="all, delete-orphan")


class SessionDB(Base):
    """Session database model."""
    __tablename__ = "sessions"
    
    token = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    user = relationship("UserDB", back_populates="sessions")


class PlatformDB(Base):
    """Platform connection database model."""
    __tablename__ = "platforms"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # aws, gcp, azure, custom
    encrypted_credentials = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_tested = Column(DateTime, nullable=True)
    connection_status = Column(String(20), default="unknown")  # connected, failed, unknown
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)


class ApiKeyDB(Base):
    """API key database model."""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    service = Column(String(50), nullable=False, index=True)  # sambanova, modal, hyperbolic, etc.
    encrypted_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)


# ============== DATABASE FUNCTIONS ==============

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get a new database session (non-generator version)."""
    return SessionLocal()


# Initialize database on import
init_db()
