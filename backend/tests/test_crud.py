"""
Unit tests for CRUD operations
Tests all database operations for users, sessions, messages, listings, and agent memory
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import crud
import models


# Test database setup
@pytest.fixture
def db():
    """Create a test database for each test"""
    # Use in-memory SQLite database for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestUserCRUD:
    """Test user CRUD operations"""

    def test_create_user(self, db):
        """Test creating a new user"""
        user = crud.create_user(
            db=db,
            email="test@example.com",
            password="password123",
            display_name="Test User"
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.password_hash != "password123"  # Should be hashed

    def test_get_user_by_email(self, db):
        """Test retrieving user by email"""
        # Create user
        crud.create_user(db=db, email="test@example.com", password="password123")

        # Retrieve user
        user = crud.get_user_by_email(db=db, email="test@example.com")

        assert user is not None
        assert user.email == "test@example.com"

    def test_get_user_by_id(self, db):
        """Test retrieving user by ID"""
        # Create user
        created_user = crud.create_user(db=db, email="test@example.com", password="password123")

        # Retrieve user
        user = crud.get_user_by_id(db=db, user_id=created_user.id)

        assert user is not None
        assert user.id == created_user.id

    def test_verify_password(self, db):
        """Test password verification"""
        # Create user
        user = crud.create_user(db=db, email="test@example.com", password="password123")

        # Test correct password
        assert crud.verify_password("password123", user.password_hash) is True

        # Test incorrect password
        assert crud.verify_password("wrongpassword", user.password_hash) is False


class TestSessionCRUD:
    """Test session CRUD operations"""

    def test_create_session(self, db):
        """Test creating a new session"""
        # Create user first
        user = crud.create_user(db=db, email="test@example.com", password="password123")

        # Create session
        session = crud.create_session(
            db=db,
            user_id=user.id,
            title="Find a car",
            category="cars"
        )

        assert session.id is not None
        assert session.user_id == user.id
        assert session.title == "Find a car"
        assert session.category == "cars"
        assert session.status == "ACTIVE"

    def test_list_sessions_by_user(self, db):
        """Test listing sessions for a user"""
        # Create user
        user = crud.create_user(db=db, email="test@example.com", password="password123")

        # Create multiple sessions
        crud.create_session(db=db, user_id=user.id, title="Session 1", category="cars")
        crud.create_session(db=db, user_id=user.id, title="Session 2", category="laptops")

        # List sessions
        sessions = crud.list_sessions_by_user(db=db, user_id=user.id)

        assert len(sessions) == 2
        assert sessions[0].title in ["Session 1", "Session 2"]

    def test_delete_session(self, db):
        """Test deleting a session"""
        # Create user and session
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")

        # Delete session
        result = crud.delete_session(db=db, session_id=session.id)

        assert result is True

        # Verify deletion
        deleted_session = crud.get_session_by_id(db=db, session_id=session.id)
        assert deleted_session is None

    def test_update_session_status(self, db):
        """Test updating session status"""
        # Create user and session
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")

        # Update status
        updated = crud.update_session_status(
            db=db,
            session_id=session.id,
            status="WAITING_FOR_CLARIFICATION",
            pending_clarification_id="test_id"
        )

        assert updated.status == "WAITING_FOR_CLARIFICATION"
        assert updated.pending_clarification_id == "test_id"


class TestListingCRUD:
    """Test listing CRUD operations"""

    def test_create_listing(self, db):
        """Test creating a new listing"""
        # Create user and session
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")

        # Create listing
        listing = crud.create_listing(
            db=db,
            session_id=session.id,
            title="2014 Mazda Miata",
            url="https://example.com",
            price=13500.00,
            currency="USD",
            marketplace="Craigslist",
            listing_metadata={"mileage": 78000}
        )

        assert listing.id is not None
        assert listing.title == "2014 Mazda Miata"
        assert listing.price == 13500.00
        assert listing.listing_metadata["mileage"] == 78000
        assert listing.status == "active"
        assert listing.score is None  # Not yet evaluated

    def test_list_listings_by_session(self, db):
        """Test listing listings for a session"""
        # Create user and session
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")

        # Create listings
        crud.create_listing(db=db, session_id=session.id, title="Listing 1")
        crud.create_listing(db=db, session_id=session.id, title="Listing 2")

        # List active listings
        listings = crud.list_listings_by_session(db=db, session_id=session.id, active_only=True)

        assert len(listings) == 2

    def test_update_listing_score(self, db):
        """Test updating listing score and rationale"""
        # Create user, session, and listing
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")
        listing = crud.create_listing(db=db, session_id=session.id, title="Test Listing")

        # Update score
        updated = crud.update_listing_score(
            db=db,
            listing_id=listing.id,
            score=75,
            rationale="Good deal, slightly above market price"
        )

        assert updated.score == 75
        assert updated.rationale == "Good deal, slightly above market price"

    def test_mark_listing_removed(self, db):
        """Test marking a listing as removed"""
        # Create user, session, and listing
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")
        listing = crud.create_listing(db=db, session_id=session.id, title="Test Listing")

        # Mark as removed
        updated = crud.mark_listing_removed(db=db, listing_id=listing.id)

        assert updated.status == "removed"

        # Verify it doesn't appear in active listings
        active_listings = crud.list_listings_by_session(db=db, session_id=session.id, active_only=True)
        assert len(active_listings) == 0


class TestMessageCRUD:
    """Test message CRUD operations"""

    def test_create_message(self, db):
        """Test creating a message"""
        # Create user and session
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")

        # Create message
        message = crud.create_message(
            db=db,
            session_id=session.id,
            sender="user",
            text="Hello, agent!",
            type="normal"
        )

        assert message.id is not None
        assert message.sender == "user"
        assert message.text == "Hello, agent!"
        assert message.type == "normal"

    def test_create_clarifying_question(self, db):
        """Test creating a clarifying question message"""
        # Create user and session
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")

        # Create clarifying question
        message = crud.create_message(
            db=db,
            session_id=session.id,
            sender="agent",
            text="What's more important: price or mileage?",
            type="clarification_question",
            is_blocking=True,
            clarification_status="pending"
        )

        assert message.type == "clarification_question"
        assert message.is_blocking is True
        assert message.clarification_status == "pending"

    def test_update_message_clarification(self, db):
        """Test updating clarification status"""
        # Create user and session
        user = crud.create_user(db=db, email="test@example.com", password="password123")
        session = crud.create_session(db=db, user_id=user.id, title="Test", category="cars")

        # Create question and answer
        question = crud.create_message(
            db=db,
            session_id=session.id,
            sender="agent",
            text="Question?",
            type="clarification_question",
            is_blocking=True,
            clarification_status="pending"
        )
        answer = crud.create_message(
            db=db,
            session_id=session.id,
            sender="user",
            text="Answer",
            type="normal"
        )

        # Update clarification
        updated = crud.update_message_clarification(
            db=db,
            message_id=question.id,
            clarification_status="answered",
            answer_message_id=answer.id
        )

        assert updated.clarification_status == "answered"
        assert updated.answer_message_id == answer.id


class TestAgentMemoryCRUD:
    """Test agent memory CRUD operations"""

    def test_upsert_agent_memory_create(self, db):
        """Test creating new agent memory"""
        memory = crud.upsert_agent_memory(
            db=db,
            key="user:123",
            type="user_preferences",
            data={"cars": {"budget_range": [8000, 15000]}}
        )

        assert memory.key == "user:123"
        assert memory.type == "user_preferences"
        assert memory.data["cars"]["budget_range"] == [8000, 15000]

    def test_upsert_agent_memory_update(self, db):
        """Test updating existing agent memory"""
        # Create initial memory
        crud.upsert_agent_memory(
            db=db,
            key="user:123",
            type="user_preferences",
            data={"cars": {"budget_range": [8000, 15000]}}
        )

        # Update memory
        updated = crud.upsert_agent_memory(
            db=db,
            key="user:123",
            type="user_preferences",
            data={"cars": {"budget_range": [10000, 20000]}}
        )

        assert updated.data["cars"]["budget_range"] == [10000, 20000]

    def test_get_agent_memory(self, db):
        """Test retrieving agent memory"""
        # Create memory
        crud.upsert_agent_memory(
            db=db,
            key="user:123",
            type="user_preferences",
            data={"test": "data"}
        )

        # Retrieve memory
        memory = crud.get_agent_memory(db=db, key="user:123")

        assert memory is not None
        assert memory.data["test"] == "data"

    def test_delete_agent_memory(self, db):
        """Test deleting agent memory"""
        # Create memory
        crud.upsert_agent_memory(
            db=db,
            key="user:123",
            type="user_preferences",
            data={"test": "data"}
        )

        # Delete memory
        result = crud.delete_agent_memory(db=db, key="user:123")

        assert result is True

        # Verify deletion
        memory = crud.get_agent_memory(db=db, key="user:123")
        assert memory is None
