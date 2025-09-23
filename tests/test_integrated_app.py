from fastapi.testclient import TestClient
from integrated_app import app  # Make sure this imports your main FastAPI app

# Create a client that can make requests
client = TestClient(app)


def test_read_root():
    """Tests the main "/" endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    # You can add more specific checks for the root message if you want
    assert "message" in response.json()


def test_say_hello():
    """Tests the new "/hello" endpoint."""
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"greeting": "Hello, this is my new endpoint!"}
