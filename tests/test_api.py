import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_root():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

def test_create_short_url():
    """Test creating a short URL"""
    response = client.post(
        "/shorten",
        json={"original_url": "https://google.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data
    assert data["original_url"] == "https://google.com"
    assert data["click_count"] == 0

def test_create_short_url_with_custom_code():
    """Test creating a short URL with custom code"""
    response = client.post(
        "/shorten",
        json={"original_url": "https://github.com", "custom_code": "github"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "github"

def test_create_duplicate_custom_code():
    """Test creating URL with duplicate custom code"""
    # First creation should succeed
    client.post(
        "/shorten",
        json={"original_url": "https://example.com", "custom_code": "example"}
    )
    
    # Second creation with same code should fail
    response = client.post(
        "/shorten",
        json={"original_url": "https://example2.com", "custom_code": "example"}
    )
    assert response.status_code == 400

def test_invalid_url():
    """Test creating short URL with invalid URL"""
    response = client.post(
        "/shorten",
        json={"original_url": "not-a-valid-url"}
    )
    assert response.status_code == 422  # Pydantic validation error

def test_redirect():
    """Test URL redirection"""
    # Create a short URL first
    create_response = client.post(
        "/shorten",
        json={"original_url": "https://python.org"}
    )
    short_code = create_response.json()["short_code"]
    
    # Test redirection
    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://python.org"

def test_get_url_info():
    """Test getting URL info"""
    # Create a short URL first
    create_response = client.post(
        "/shorten",
        json={"original_url": "https://fastapi.tiangolo.com"}
    )
    short_code = create_response.json()["short_code"]
    
    # Get URL info
    response = client.get(f"/api/urls/{short_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://fastapi.tiangolo.com"
    assert data["short_code"] == short_code

def test_get_analytics():
    """Test getting analytics"""
    # Create a short URL first
    create_response = client.post(
        "/shorten",
        json={"original_url": "https://stackoverflow.com"}
    )
    short_code = create_response.json()["short_code"]
    
    # Make a few requests to generate analytics
    client.get(f"/{short_code}", follow_redirects=False)
    client.get(f"/{short_code}", follow_redirects=False)
    
    # Get analytics
    response = client.get(f"/api/analytics/{short_code}")
    assert response.status_code == 200
    data = response.json()
    assert "total_clicks" in data
    assert "unique_ips" in data
    assert data["total_clicks"] >= 2

def test_list_urls():
    """Test listing URLs"""
    response = client.get("/api/urls")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_nonexistent_short_code():
    """Test accessing nonexistent short code"""
    response = client.get("/nonexistent", follow_redirects=False)
    assert response.status_code == 404

def test_nonexistent_analytics():
    """Test analytics for nonexistent short code"""
    response = client.get("/api/analytics/nonexistent")
    assert response.status_code == 404
