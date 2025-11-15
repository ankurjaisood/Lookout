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
            json={"title": "Find a car", "category": "cars"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Find a car"
        assert data["category"] == "cars"
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
                "marketplace": "Craigslist"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "2014 Mazda Miata"
        assert data["price"] == 13500.0

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
