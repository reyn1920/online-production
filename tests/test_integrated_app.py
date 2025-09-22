from fastapi.testclient import TestClient
from integrated_app import app  # Import the "app" from your main file

# Create a test client that can make requests to your app
client = TestClient(app)

def test_say_hello():
    # Make a GET request to the "/hello" endpoint
    response = client.get("/hello")
    
    # Assert that the HTTP status code is 200 (OK)
    assert response.status_code == 200
    
    # Assert that the response JSON is exactly what we expect
    assert response.json() == {"greeting": "Hello, this is my new endpoint!"}
