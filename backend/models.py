"""
SQLAlchemy database models
Implements all tables from docs/lookout_design.md Section 4

This module defines the database schema using SQLAlchemy ORM.
All tables are defined as classes inheriting from Base.

Database Tables:
- User: User accounts with authentication
- Session: Research sessions for organizing listings
- Message: Chat messages between user and agent
- Listing: Marketplace listings being evaluated
- AgentMemory: Agent memory (preferences & session summaries)

Key Relationships:
- User → Sessions (one-to-many)
- Session → Messages (one-to-many)
- Session → Listings (one-to-many)

All IDs are UUIDs stored as strings for portability.
Timestamps are automatically managed with server_default and onupdate.
"""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid


def generate_uuid():
    """
    Generate a new UUID v4 as a string

    Returns:
        String representation of a UUID v4
    """
    return str(uuid.uuid4())


class User(Base):
    """
    User model - Section 4.1

    Represents a user account with email/password authentication.

    Attributes:
        id: UUID primary key
        email: Unique email address for login
        password_hash: Bcrypt hashed password
        display_name: Optional display name
        created_at: Account creation timestamp
        updated_at: Last update timestamp

    Relationships:
        sessions: All research sessions created by this user
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Session model - Section 4.2"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g. 'cars', 'laptops'
    requirements = Column(Text, nullable=True)  # User-provided global requirements for the session
    status = Column(String, nullable=False, default="ACTIVE")  # ACTIVE | WAITING_FOR_CLARIFICATION | CLOSED
    pending_clarification_id = Column(String, ForeignKey("messages.id"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", foreign_keys="Message.session_id", cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="session", cascade="all, delete-orphan")
    pending_clarification = relationship("Message", foreign_keys=[pending_clarification_id], post_update=True)


class Message(Base):
    """Message model - Section 4.3"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String, nullable=False)  # 'user' | 'agent'
    type = Column(String, nullable=False, default="normal")  # 'normal' | 'clarification_question'
    text = Column(Text, nullable=False)
    is_blocking = Column(Boolean, nullable=False, default=False)
    clarification_status = Column(String, nullable=True)  # 'pending' | 'answered' | 'skipped'
    answer_message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    target_listing_id = Column(String, ForeignKey("listings.id"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="messages", foreign_keys=[session_id])
    answer_message = relationship("Message", remote_side=[id], foreign_keys=[answer_message_id])
    target_listing = relationship("Listing", foreign_keys=[target_listing_id])


class Listing(Base):
    """Listing model - Section 4.4"""
    __tablename__ = "listings"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    url = Column(String)
    price = Column(Numeric(12, 2))
    currency = Column(String)
    marketplace = Column(String)
    listing_metadata = Column(JSON)  # Arbitrary per-category fields (renamed from 'metadata' which is reserved)
    description = Column(Text, nullable=True)  # Pasted listing description text
    status = Column(String, nullable=False, default="active")  # 'active' | 'removed'

    # Agent evaluation fields
    score = Column(Integer, nullable=True)  # 0-100; null until evaluated
    rationale = Column(Text, nullable=True)  # Explanation from agent

    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    session = relationship("Session", back_populates="listings")


class AgentMemory(Base):
    """Agent Memory model - Section 4.5
    Logically owned by Agent Interface
    """
    __tablename__ = "agent_memory"

    key = Column(String, primary_key=True)  # e.g. 'user:{user_id}', 'session:{session_id}'
    type = Column(String, nullable=False)  # 'user_preferences' | 'session_summary'
    data = Column(JSON, nullable=False)  # Structured JSON (preferences/summary)
    last_updated = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
