"""
Database CRUD operations
Task 1.2: Database Access Layer

This module provides all database CRUD (Create, Read, Update, Delete) operations
for the Lookout application. It acts as the data access layer between the API
routes and the database models.

Key Responsibilities:
- User management (creation, authentication)
- Session management (CRUD operations)
- Message handling (chat history, clarifications)
- Listing management (create, update scores, mark removed)
- Agent memory operations (preferences, session summaries)

All functions accept a SQLAlchemy Session object and return model instances or None.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
import models
from passlib.context import CryptContext

# Password hashing context using bcrypt
# This ensures passwords are securely hashed before storage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============= User CRUD =============

def create_user(db: Session, email: str, password: str, display_name: Optional[str] = None) -> models.User:
    """
    Create a new user with hashed password

    Args:
        db: Database session
        email: User's email address (must be unique)
        password: Plain text password (will be hashed)
        display_name: Optional display name for the user

    Returns:
        User: The created user object with generated ID

    Note:
        Password is automatically hashed using bcrypt before storage
    """
    hashed_password = pwd_context.hash(password)
    db_user = models.User(
        email=email,
        password_hash=hashed_password,
        display_name=display_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Retrieve a user by their email address

    Args:
        db: Database session
        email: Email address to search for

    Returns:
        User object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[models.User]:
    """
    Retrieve a user by their ID

    Args:
        db: Database session
        user_id: UUID string of the user

    Returns:
        User object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password

    Args:
        plain_password: Password provided by user
        hashed_password: Bcrypt hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============= Session CRUD =============

def create_session(
    db: Session,
    user_id: str,
    title: str,
    category: str,
    requirements: Optional[str] = None
) -> models.Session:
    """Create a new session"""
    db_session = models.Session(
        user_id=user_id,
        title=title,
        category=category,
        requirements=requirements,
        status="ACTIVE"
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def list_sessions_by_user(db: Session, user_id: str) -> List[models.Session]:
    """List all sessions for a user"""
    return db.query(models.Session).filter(
        models.Session.user_id == user_id
    ).order_by(desc(models.Session.created_at)).all()


def get_session_by_id(db: Session, session_id: str) -> Optional[models.Session]:
    """Get session by ID"""
    return db.query(models.Session).filter(models.Session.id == session_id).first()


def delete_session(db: Session, session_id: str) -> bool:
    """Delete a session (cascades to messages and listings)"""
    db_session = get_session_by_id(db, session_id)
    if db_session:
        # Delete agent memory for this session
        delete_agent_memory(db, f"session:{session_id}")
        db.delete(db_session)
        db.commit()
        return True
    return False


def update_session(
    db: Session,
    session_id: str,
    title: Optional[str] = None,
    category: Optional[str] = None,
    requirements: Optional[str] = None
) -> Optional[models.Session]:
    """Update session metadata fields"""
    db_session = get_session_by_id(db, session_id)
    if not db_session:
        return None

    if title is not None:
        db_session.title = title
    if category is not None:
        db_session.category = category
    if requirements is not None:
        db_session.requirements = requirements

    db.commit()
    db.refresh(db_session)
    return db_session


def update_session_status(db: Session, session_id: str, status: str, pending_clarification_id: Optional[str] = None) -> Optional[models.Session]:
    """Update session status and pending clarification"""
    db_session = get_session_by_id(db, session_id)
    if db_session:
        db_session.status = status
        db_session.pending_clarification_id = pending_clarification_id
        db.commit()
        db.refresh(db_session)
    return db_session


# ============= Message CRUD =============

def create_message(
    db: Session,
    session_id: str,
    sender: str,
    text: str,
    type: str = "normal",
    is_blocking: bool = False,
    clarification_status: Optional[str] = None
) -> models.Message:
    """Create a new message"""
    db_message = models.Message(
        session_id=session_id,
        sender=sender,
        type=type,
        text=text,
        is_blocking=is_blocking,
        clarification_status=clarification_status
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def list_messages_by_session(db: Session, session_id: str, limit: Optional[int] = None) -> List[models.Message]:
    """List messages for a session"""
    query = db.query(models.Message).filter(
        models.Message.session_id == session_id
    ).order_by(models.Message.created_at)

    if limit:
        query = query.limit(limit)

    return query.all()


def update_message_clarification(
    db: Session,
    message_id: str,
    clarification_status: str,
    answer_message_id: Optional[str] = None
) -> Optional[models.Message]:
    """Update clarification status of a message"""
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if db_message:
        db_message.clarification_status = clarification_status
        if answer_message_id:
            db_message.answer_message_id = answer_message_id
        db.commit()
        db.refresh(db_message)
    return db_message


# ============= Listing CRUD =============

def create_listing(
    db: Session,
    session_id: str,
    title: str,
    url: Optional[str] = None,
    price: Optional[float] = None,
    currency: Optional[str] = None,
    marketplace: Optional[str] = None,
    listing_metadata: Optional[dict] = None
) -> models.Listing:
    """Create a new listing"""
    db_listing = models.Listing(
        session_id=session_id,
        title=title,
        url=url,
        price=price,
        currency=currency,
        marketplace=marketplace,
        listing_metadata=listing_metadata or {}
    )
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


def list_listings_by_session(db: Session, session_id: str, active_only: bool = True) -> List[models.Listing]:
    """List listings for a session"""
    query = db.query(models.Listing).filter(models.Listing.session_id == session_id)

    if active_only:
        query = query.filter(models.Listing.status == "active")

    # Sort by score descending, nulls last
    return query.order_by(
        models.Listing.score.desc().nullslast(),
        models.Listing.created_at.desc()
    ).all()


def get_listing_by_id(db: Session, listing_id: str) -> Optional[models.Listing]:
    """Get listing by ID"""
    return db.query(models.Listing).filter(models.Listing.id == listing_id).first()


def update_listing_score(
    db: Session,
    listing_id: str,
    score: int,
    rationale: str
) -> Optional[models.Listing]:
    """Update listing score and rationale"""
    db_listing = get_listing_by_id(db, listing_id)
    if db_listing:
        db_listing.score = score
        db_listing.rationale = rationale
        db.commit()
        db.refresh(db_listing)
    return db_listing


def mark_listing_removed(db: Session, listing_id: str) -> Optional[models.Listing]:
    """Mark a listing as removed"""
    db_listing = get_listing_by_id(db, listing_id)
    if db_listing:
        db_listing.status = "removed"
        db.commit()
        db.refresh(db_listing)
    return db_listing


# ============= Agent Memory CRUD =============

def get_agent_memory(db: Session, key: str) -> Optional[models.AgentMemory]:
    """Get agent memory by key"""
    return db.query(models.AgentMemory).filter(models.AgentMemory.key == key).first()


def upsert_agent_memory(db: Session, key: str, type: str, data: dict) -> models.AgentMemory:
    """Insert or update agent memory"""
    db_memory = get_agent_memory(db, key)

    if db_memory:
        # Update existing
        db_memory.type = type
        db_memory.data = data
    else:
        # Create new
        db_memory = models.AgentMemory(
            key=key,
            type=type,
            data=data
        )
        db.add(db_memory)

    db.commit()
    db.refresh(db_memory)
    return db_memory


def delete_agent_memory(db: Session, key: str) -> bool:
    """Delete agent memory by key"""
    db_memory = get_agent_memory(db, key)
    if db_memory:
        db.delete(db_memory)
        db.commit()
        return True
    return False
