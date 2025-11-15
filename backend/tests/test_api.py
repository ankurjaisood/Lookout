"""
API integration tests
Tests all API endpoints with proper authentication
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
import models  # Import models to ensure they're registered with Base
from main import app
from agent.schemas import AgentResponse, AgentMessage


# Test database setup
@pytest.fixture(scope="function")
def db_connection():
    """Create a database connection that persists for the whole test"""
    # Use a connection-level fixture to ensure the in-memory DB persists
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=None  # Disable pooling for testing
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create a connection
    connection = engine.connect()

    yield connection

    # Cleanup
    connection.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(db_connection):
    """Create test database session using the connection"""
    # Create a transaction
    transaction = db_connection.begin()

    # Create session bound to the connection
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_connection)
    db = TestingSessionLocal()

    yield db

    # Rollback and cleanup
    db.close()
    transaction.rollback()


@pytest.fixture
def client(test_db, db_connection):
    """Create test client with database override"""
    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close - managed by test_db fixture

    app.dependency_overrides[get_db] = override_get_db

    # Create client
    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


class TestAuthAPI:
    """Test authentication endpoints"""

    def test_signup(self, client):
        """Test user signup"""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "password123",
                "display_name": "Test User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["display_name"] == "Test User"
        assert "id" in data

    def test_signup_duplicate_email(self, client):
        """Test signup with duplicate email"""
        # Create first user
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )

        # Try to create duplicate
        response = client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )

        assert response.status_code == 409

    def test_login(self, client):
        """Test user login"""
        # Create user
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )

        # Login
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrong"}
        )

        assert response.status_code == 401

    def test_logout(self, client):
        """Test logout"""
        response = client.post("/api/auth/logout")
        assert response.status_code == 200

    def test_get_me(self, client):
        """Test getting current user"""
        # Create and login user
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )

        # Get current user
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"


class TestSessionAPI:
    """Test session endpoints"""

    @pytest.fixture
    def authenticated_client(self, client):
        """Create authenticated client"""
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )
        return client

    def test_create_session(self, authenticated_client):
        """Test creating a session"""
        response = authenticated_client.post(
            "/api/sessions",
            json={
                "title": "Find a car",
                "category": "cars",
                "requirements": "Manual transmission, under 50k miles"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Find a car"
        assert data["category"] == "cars"
        assert data["requirements"] == "Manual transmission, under 50k miles"
        assert data["status"] == "ACTIVE"

    def test_list_sessions(self, authenticated_client):
        """Test listing sessions"""
        # Create sessions
        authenticated_client.post(
            "/api/sessions",
            json={"title": "Session 1", "category": "cars"}
        )
        authenticated_client.post(
            "/api/sessions",
            json={"title": "Session 2", "category": "laptops"}
        )

        # List sessions
        response = authenticated_client.get("/api/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_session(self, authenticated_client):
        """Test getting a specific session"""
        # Create session
        create_response = authenticated_client.post(
            "/api/sessions",
            json={"title": "Test Session", "category": "cars"}
        )
        session_id = create_response.json()["id"]

        # Get session
        response = authenticated_client.get(f"/api/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Session"
        assert data["requirements"] is None

    def test_update_session_requirements(self, authenticated_client):
        """Test updating session requirements"""
        create_response = authenticated_client.post(
            "/api/sessions",
            json={"title": "Miata hunt", "category": "cars"}
        )
        session_id = create_response.json()["id"]

        update_response = authenticated_client.patch(
            f"/api/sessions/{session_id}",
            json={"requirements": "Manual, hardtop, <50k miles"}
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["requirements"] == "Manual, hardtop, <50k miles"

    def test_delete_session(self, authenticated_client):
        """Test deleting a session"""
        # Create session
        create_response = authenticated_client.post(
            "/api/sessions",
            json={"title": "Test Session", "category": "cars"}
        )
        session_id = create_response.json()["id"]

        # Delete session
        response = authenticated_client.delete(f"/api/sessions/{session_id}")

        assert response.status_code == 204

        # Verify deletion
        get_response = authenticated_client.get(f"/api/sessions/{session_id}")
        assert get_response.status_code == 404


class TestListingAPI:
    """Test listing endpoints"""

    @pytest.fixture(autouse=True)
    def stub_agent(self, monkeypatch):
        """Default stub for agent evaluations used by create/update endpoints"""
        def fake_process_request(self, request):
            return AgentResponse(
                agent_message=AgentMessage(text="Stub evaluation."),
                actions=[]
            )
        monkeypatch.setattr(
            "routes.listing_routes.AgentService.process_request",
            fake_process_request
        )

    @pytest.fixture
    def authenticated_client_with_session(self, client):
        """Create authenticated client with a session"""
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )
        session_response = client.post(
            "/api/sessions",
            json={"title": "Test Session", "category": "cars"}
        )
        session_id = session_response.json()["id"]
        client.session_id = session_id
        return client

    def test_create_listing(self, authenticated_client_with_session):
        """Test creating a listing"""
        client = authenticated_client_with_session
        session_id = client.session_id

        response = client.post(
            f"/api/sessions/{session_id}/listings",
            json={
                "title": "2014 Mazda Miata",
                "url": "https://example.com",
                "price": 13500,
                "currency": "USD",
                "marketplace": "Craigslist",
                "description": "Great car"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "2014 Mazda Miata"
        assert data["price"] == 13500.0
        assert data["description"] == "Great car"

    def test_list_listings(self, authenticated_client_with_session):
        """Test listing listings"""
        client = authenticated_client_with_session
        session_id = client.session_id

        # Create listings
        client.post(
            f"/api/sessions/{session_id}/listings",
            json={"title": "Listing 1", "price": 10000}
        )
        client.post(
            f"/api/sessions/{session_id}/listings",
            json={"title": "Listing 2", "price": 15000}
        )

        # List listings
        response = client.get(f"/api/sessions/{session_id}/listings")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_mark_listing_removed(self, authenticated_client_with_session):
        """Test marking listing as removed"""
        client = authenticated_client_with_session
        session_id = client.session_id

        # Create listing
        create_response = client.post(
            f"/api/sessions/{session_id}/listings",
            json={"title": "Test Listing"}
        )
        listing_id = create_response.json()["id"]

        # Mark as removed
        response = client.patch(f"/api/sessions/{session_id}/listings/{listing_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "removed"

    def test_update_listing(self, authenticated_client_with_session, monkeypatch):
        """Test updating listing details"""
        client = authenticated_client_with_session
        session_id = client.session_id

        create_response = client.post(
            f"/api/sessions/{session_id}/listings",
            json={"title": "Original"}
        )
        listing_id = create_response.json()["id"]

        call_info = {"count": 0}

        def fake_process_request(self, request):
            call_info["count"] += 1
            return AgentResponse(
                agent_message=AgentMessage(text="Updated."),
                actions=[]
            )

        monkeypatch.setattr(
            "routes.listing_routes.AgentService.process_request",
            fake_process_request
        )

        response = client.put(
            f"/api/sessions/{session_id}/listings/{listing_id}",
            json={
                "title": "Updated title",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"
        assert data["description"] == "Updated description"
        assert call_info["count"] == 1

    def test_reevaluate_listing(self, authenticated_client_with_session, monkeypatch):
        """Test manual listing reevaluation triggers agent workflow"""
        client = authenticated_client_with_session
        session_id = client.session_id

        # Create listing to evaluate
        create_response = client.post(
            f"/api/sessions/{session_id}/listings",
            json={"title": "Reloadable Listing"}
        )
        listing_id = create_response.json()["id"]

        def fake_process_request(self, request):
            return AgentResponse(
                agent_message=AgentMessage(text="Updated scores."),
                actions=[
                    {
                        "type": "UPDATE_EVALUATIONS",
                        "evaluations": [
                            {
                                "listing_id": listing_id,
                                "score": 88,
                                "rationale": "Manual refresh complete."
                            }
                        ]
                    }
                ]
            )

        monkeypatch.setattr(
            "routes.listing_routes.AgentService.process_request",
            fake_process_request
        )

        response = client.post(f"/api/sessions/{session_id}/listings/{listing_id}/reevaluate")

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 88
        assert "Manual refresh" in data["rationale"]


class TestClarificationsAPI:
    """Test clarifications endpoints"""

    @pytest.fixture
    def authenticated_client_with_listing(self, client):
        """Create authenticated client with session and listing"""
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )
        session_response = client.post(
            "/api/sessions",
            json={"title": "Test Session", "category": "cars"}
        )
        session_id = session_response.json()["id"]
        listing_response = client.post(
            f"/api/sessions/{session_id}/listings",
            json={"title": "Listing 1"}
        )
        listing_id = listing_response.json()["id"]
        client.session_id = session_id
        client.listing_id = listing_id
        return client

    @pytest.fixture
    def authenticated_client_with_two_listings(self, client):
        """Create authenticated client with two listings"""
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )
        session_response = client.post(
            "/api/sessions",
            json={"title": "Test Session", "category": "cars"}
        )
        session_id = session_response.json()["id"]
        listing1 = client.post(
            f"/api/sessions/{session_id}/listings",
            json={"title": "Listing 1"}
        ).json()["id"]
        listing2 = client.post(
            f"/api/sessions/{session_id}/listings",
            json={"title": "Listing 2"}
        ).json()["id"]
        client.session_id = session_id
        client.listing_ids = [listing1, listing2]
        return client

    def test_listing_level_clarification_flow(self, authenticated_client_with_listing, monkeypatch):
        """Verify clarifying questions appear under listings and can be answered inline"""
        client = authenticated_client_with_listing
        session_id = client.session_id
        listing_id = client.listing_id

        def fake_process_request(self, request):
            if "50k miles" in request.user_message.text:
                return AgentResponse(
                    agent_message=AgentMessage(text="Thanks for clarifying."),
                    actions=[
                        {
                            "type": "UPDATE_EVALUATIONS",
                            "evaluations": [
                                {
                                    "listing_id": listing_id,
                                    "score": 90,
                                    "rationale": "Clarification received."
                                }
                            ]
                        }
                    ]
                )
            return AgentResponse(
                agent_message=AgentMessage(text="Need mileage info."),
                actions=[
                    {
                        "type": "ASK_CLARIFYING_QUESTION",
                        "question": "How many miles are on this listing?",
                        "blocking": True
                    }
                ]
            )

        monkeypatch.setattr(
            "routes.message_routes.AgentService.process_request",
            fake_process_request
        )

        # Trigger clarifying question
        response = client.post(
            f"/api/sessions/{session_id}/messages",
            json={"text": "Please evaluate this listing"}
        )
        assert response.status_code == 201

        # Fetch state and verify clarification is attached to listing
        state = client.get(f"/api/sessions/{session_id}/state").json()
        listing = next(item for item in state["listings"] if item["id"] == listing_id)
        assert len(listing["clarifications"]) == 1
        clarification_id = listing["clarifications"][0]["id"]
        assert listing["clarifications"][0]["clarification_status"] == "pending"

        # Answer clarification inline
        answer_response = client.post(
            f"/api/sessions/{session_id}/clarifications/{clarification_id}/answer",
            json={"text": "It has 50k miles"}
        )
        assert answer_response.status_code == 201

        # Clarification should be answered and listing re-evaluated
        updated_state = client.get(f"/api/sessions/{session_id}/state").json()
        updated_listing = next(item for item in updated_state["listings"] if item["id"] == listing_id)
        clarification = updated_listing["clarifications"][0]
        assert clarification["clarification_status"] == "answered"
        assert clarification["answer_text"] == "It has 50k miles"
        assert updated_listing["score"] == 90

    def test_listing_clarification_from_reevaluate_without_listing_id(self, authenticated_client_with_listing, monkeypatch):
        """Ensure clarifications from manual reevaluation are linked even without listing_id in action"""
        client = authenticated_client_with_listing
        session_id = client.session_id
        listing_id = client.listing_id

        def fake_process_request(self, request):
            if "50k miles" in request.user_message.text:
                return AgentResponse(
                    agent_message=AgentMessage(text="Thanks for clarifying."),
                    actions=[
                        {
                            "type": "UPDATE_EVALUATIONS",
                            "evaluations": [
                                {
                                    "listing_id": listing_id,
                                    "score": 92,
                                    "rationale": "Clarification applied."
                                }
                            ]
                        }
                    ]
                )
            return AgentResponse(
                agent_message=AgentMessage(text="Need mileage info."),
                actions=[
                    {
                        "type": "ASK_CLARIFYING_QUESTION",
                        "question": "How many miles are on this listing?",
                        "blocking": True
                    }
                ]
            )

        monkeypatch.setattr(
            "routes.listing_routes.AgentService.process_request",
            fake_process_request
        )

        response = client.post(f"/api/sessions/{session_id}/listings/{listing_id}/reevaluate")
        assert response.status_code == 200

        state = client.get(f"/api/sessions/{session_id}/state").json()
        listing = next(item for item in state["listings"] if item["id"] == listing_id)
        assert len(listing["clarifications"]) == 1
        clarification_id = listing["clarifications"][0]["id"]

        client.post(
            f"/api/sessions/{session_id}/clarifications/{clarification_id}/answer",
            json={"text": "It has 50k miles"}
        )

        updated_state = client.get(f"/api/sessions/{session_id}/state").json()
        updated_listing = next(item for item in updated_state["listings"] if item["id"] == listing_id)
        clarification = updated_listing["clarifications"][0]
        assert clarification["clarification_status"] == "answered"
        assert updated_listing["score"] == 92

    def test_multiple_clarifications_same_response(self, authenticated_client_with_two_listings, monkeypatch):
        """Agent can return multiple clarifications at once"""
        client = authenticated_client_with_two_listings
        session_id = client.session_id
        listing_a, listing_b = client.listing_ids
        call_count = {"count": 0}

        def fake_process_request(self, request):
            call_count["count"] += 1
            if call_count["count"] == 1:
                return AgentResponse(
                    agent_message=AgentMessage(text="Need more info."),
                    actions=[
                        {
                            "type": "ASK_CLARIFYING_QUESTION",
                            "question": "What's the mileage for Listing 1?",
                            "blocking": True,
                            "listing_id": listing_a
                        },
                        {
                            "type": "ASK_CLARIFYING_QUESTION",
                            "question": "Any accident history for Listing 2?",
                            "blocking": True,
                            "listing_id": listing_b
                        }
                    ]
                )
            else:
                return AgentResponse(
                    agent_message=AgentMessage(text="Thanks!"),
                    actions=[]
                )

        monkeypatch.setattr(
            "routes.message_routes.AgentService.process_request",
            fake_process_request
        )

        client.post(
            f"/api/sessions/{session_id}/messages",
            json={"text": "Evaluate both listings"}
        )

        state = client.get(f"/api/sessions/{session_id}/state").json()
        listing_state_map = {listing["id"]: listing for listing in state["listings"]}
        assert len(listing_state_map[listing_a]["clarifications"]) == 1
        assert len(listing_state_map[listing_b]["clarifications"]) == 1

        clar_a = listing_state_map[listing_a]["clarifications"][0]
        clar_b = listing_state_map[listing_b]["clarifications"][0]

        client.post(
            f"/api/sessions/{session_id}/clarifications/{clar_a['id']}/answer",
            json={"text": "50k miles"}
        )

        state_after_first = client.get(f"/api/sessions/{session_id}/state").json()
        listing_b_state = next(item for item in state_after_first["listings"] if item["id"] == listing_b)
        assert listing_b_state["clarifications"][0]["clarification_status"] == "pending"

        client.post(
            f"/api/sessions/{session_id}/clarifications/{clar_b['id']}/answer",
            json={"text": "Clean history"}
        )

        final_state = client.get(f"/api/sessions/{session_id}/state").json()
        listing_final = {l["id"]: l for l in final_state["listings"]}
        assert listing_final[listing_a]["clarifications"][0]["clarification_status"] == "answered"
        assert listing_final[listing_b]["clarifications"][0]["clarification_status"] == "answered"
