"""
Agent Interface tests
Tests agent memory, prompt building, and action processing
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from agent.memory import AgentMemory
from agent.prompts import PromptBuilder
from agent.schemas import SessionContext, UserInfo, SessionInfo, MessageInfo, ListingInfo


@pytest.fixture
def db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestAgentMemory:
    """Test agent memory management"""

    def test_load_user_preferences_empty(self, db):
        """Test loading preferences for new user"""
        memory = AgentMemory(db)
        preferences = memory.load_user_preferences("user_123")

        assert preferences is not None
        assert "categories" in preferences
        assert preferences["summary"] is None

    def test_save_and_load_user_preferences(self, db):
        """Test saving and loading user preferences"""
        memory = AgentMemory(db)

        # Save preferences
        prefs = {
            "categories": {
                "cars": {"budget_range": [8000, 15000], "important_factors": ["reliability"]}
            },
            "summary": "Prefers reliable cars within budget"
        }
        memory.save_user_preferences("user_123", prefs)

        # Load preferences
        loaded = memory.load_user_preferences("user_123")

        assert loaded["categories"]["cars"]["budget_range"] == [8000, 15000]
        assert loaded["summary"] == "Prefers reliable cars within budget"

    def test_update_user_preferences(self, db):
        """Test updating user preferences"""
        memory = AgentMemory(db)

        # Save initial preferences
        memory.save_user_preferences("user_123", {
            "categories": {"cars": {"budget_range": [8000, 15000]}},
            "summary": None
        })

        # Update preferences
        memory.update_user_preferences("user_123", {
            "categories": {"cars": {"important_factors": ["fuel_economy"]}},
            "summary": "Wants fuel efficient cars"
        })

        # Load and verify
        loaded = memory.load_user_preferences("user_123")

        assert "budget_range" in loaded["categories"]["cars"]
        assert loaded["categories"]["cars"]["important_factors"] == ["fuel_economy"]
        assert loaded["summary"] == "Wants fuel efficient cars"

    def test_load_session_summary_empty(self, db):
        """Test loading summary for new session"""
        memory = AgentMemory(db)
        summary = memory.load_session_summary("session_123")

        assert summary is not None
        assert "requirements" in summary
        assert summary["summary"] is None

    def test_save_and_load_session_summary(self, db):
        """Test saving and loading session summary"""
        memory = AgentMemory(db)

        # Save summary
        summary = {
            "requirements": ["manual transmission", "under $15k"],
            "summary": "Looking for affordable manual Miata",
            "top_listing_ids": ["listing_1", "listing_2"],
            "open_questions": []
        }
        memory.save_session_summary("session_123", summary)

        # Load summary
        loaded = memory.load_session_summary("session_123")

        assert loaded["requirements"] == ["manual transmission", "under $15k"]
        assert loaded["summary"] == "Looking for affordable manual Miata"
        assert len(loaded["top_listing_ids"]) == 2

    def test_update_session_summary(self, db):
        """Test updating session summary"""
        memory = AgentMemory(db)

        # Create initial summary
        memory.save_session_summary("session_123", {
            "requirements": [],
            "summary": None,
            "top_listing_ids": [],
            "open_questions": []
        })

        # Update summary
        memory.update_session_summary(
            session_id="session_123",
            requirements=["manual transmission"],
            summary="Looking for manual Miata",
            top_listing_ids=["listing_1"]
        )

        # Load and verify
        loaded = memory.load_session_summary("session_123")

        assert loaded["requirements"] == ["manual transmission"]
        assert loaded["summary"] == "Looking for manual Miata"
        assert loaded["top_listing_ids"] == ["listing_1"]

    def test_delete_session_memory(self, db):
        """Test deleting session memory"""
        memory = AgentMemory(db)

        # Create memory
        memory.save_session_summary("session_123", {
            "requirements": [],
            "summary": None,
            "top_listing_ids": [],
            "open_questions": []
        })

        # Delete memory
        memory.delete_session_memory("session_123")

        # Verify it's reset to default
        loaded = memory.load_session_summary("session_123")
        assert loaded["summary"] is None


class TestPromptBuilder:
    """Test prompt building functionality"""

    def test_build_system_prompt(self):
        """Test system prompt generation"""
        prompt = PromptBuilder.build_system_prompt()

        assert "marketplace research assistant" in prompt.lower()
        assert "0-100" in prompt
        assert "horrible deal" in prompt.lower()
        assert "great deal" in prompt.lower()

    def test_build_user_context_with_preferences(self):
        """Test building user context with preferences"""
        preferences = {
            "categories": {"cars": {"budget_range": [8000, 15000]}}
        }

        context = PromptBuilder.build_user_context(
            user_preferences=preferences,
            session_summary=None
        )

        assert "User Preferences" in context
        assert "budget_range" in context

    def test_build_session_context_text(self):
        """Test building session context text"""
        context = SessionContext(
            user=UserInfo(id="user_123"),
            session=SessionInfo(
                id="session_123",
                title="Find a car",
                category="cars",
                status="ACTIVE",
                requirements="Manual transmission, under 50k miles"
            ),
            recent_messages=[
                MessageInfo(
                    id="msg_1",
                    sender="user",
                    text="I want a reliable car",
                    type="normal",
                    created_at="2025-11-15T10:00:00"
                )
            ],
            listings=[
                ListingInfo(
                    id="listing_1",
                    title="2014 Mazda Miata",
                    url="https://example.com",
                    price=13500.0,
                    currency="USD",
                    marketplace="Craigslist",
                    listing_metadata={"mileage": 78000},
                    description="Clean title, 78k miles, manual transmission.",
                    score=None,
                    rationale=None
                )
            ]
        )

        text = PromptBuilder.build_session_context_text(context)

        assert "Find a car" in text
        assert "cars" in text
        assert "Manual transmission, under 50k miles" in text
        assert "I want a reliable car" in text
        assert "2014 Mazda Miata" in text
        assert "13500" in text
        assert "Clean title" in text

    def test_build_full_prompt(self):
        """Test building complete prompt"""
        context = SessionContext(
            user=UserInfo(id="user_123"),
            session=SessionInfo(
                id="session_123",
                title="Find a car",
                category="cars",
                status="ACTIVE",
                requirements=None
            ),
            recent_messages=[],
            listings=[]
        )

        prompt = PromptBuilder.build_full_prompt(
            user_message="Evaluate these listings",
            session_context=context,
            user_preferences=None,
            session_summary=None
        )

        assert "marketplace research assistant" in prompt.lower()
        assert "Find a car" in prompt
        assert "Evaluate these listings" in prompt
        assert "Respond with JSON" in prompt


class TestAgentActionProcessing:
    """Test agent action processing logic"""

    def test_evaluation_action_structure(self):
        """Test that evaluation actions have correct structure"""
        action = {
            "type": "UPDATE_EVALUATIONS",
            "evaluations": [
                {
                    "listing_id": "listing_1",
                    "score": 75,
                    "rationale": "Good deal"
                }
            ]
        }

        assert action["type"] == "UPDATE_EVALUATIONS"
        assert len(action["evaluations"]) == 1
        assert action["evaluations"][0]["score"] == 75

    def test_clarifying_question_action_structure(self):
        """Test clarifying question action structure"""
        action = {
            "type": "ASK_CLARIFYING_QUESTION",
            "question": "What's more important: price or mileage?",
            "blocking": True
        }

        assert action["type"] == "ASK_CLARIFYING_QUESTION"
        assert "question" in action
        assert action["blocking"] is True

    def test_preference_update_action_structure(self):
        """Test preference update action structure"""
        action = {
            "type": "UPDATE_PREFERENCES",
            "preference_patch": {
                "categories": {
                    "cars": {"important_factors": ["reliability"]}
                }
            }
        }

        assert action["type"] == "UPDATE_PREFERENCES"
        assert "preference_patch" in action
        assert "categories" in action["preference_patch"]
