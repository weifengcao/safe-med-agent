from fastapi.testclient import TestClient
from safe_med_agent import app
import json

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("Health check passed.")

def test_normal_note():
    payload = {"patient_id": "123", "note": "Patient came in for a routine checkup."}
    response = client.post("/v1/summarize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "request_id" in data
    # Verify Middleware
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"] == data["request_id"]
    print("Normal note test passed.")

def test_emergency_note():
    payload = {"patient_id": "123", "note": "Patient expressed feelings of suicide."}
    response = client.post("/v1/summarize", json=payload)
    assert response.status_code == 451
    assert response.json() == {"error": "Emergency protocol triggered"}
    print("Emergency note test passed.")

def test_cardiac_arrest_note():
    payload = {"patient_id": "123", "note": "Patient had a cardiac arrest yesterday."}
    response = client.post("/v1/summarize", json=payload)
    assert response.status_code == 451
    assert response.json() == {"error": "Emergency protocol triggered"}
    print("Cardiac arrest note test passed.")

def test_max_length_validation():
    # Create a note slightly longer than 100,000 chars
    long_note = "a" * 100001
    payload = {"patient_id": "123", "note": long_note}
    response = client.post("/v1/summarize", json=payload)
    assert response.status_code == 422
    print("Max length validation test passed.")

if __name__ == "__main__":
    try:
        test_health()
        test_normal_note()
        test_emergency_note()
        test_cardiac_arrest_note()
        test_max_length_validation()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        exit(1)
