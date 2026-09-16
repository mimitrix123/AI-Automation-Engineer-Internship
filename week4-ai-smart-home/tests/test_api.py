from fastapi.testclient import TestClient
from dashboard.app import app

client = TestClient(app)

def test_status_endpoint():
    response = client.get('/api/status')
    assert response.status_code == 200
    assert 'temperature' in response.json()

def test_telemetry_endpoint():
    response = client.post('/api/telemetry', json={'temperature': 24.5, 'motion': True, 'light': 70, 'sound': 10, 'occupied': True})
    assert response.status_code == 200
    assert response.json()['ok'] is True
