from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_docs():
    res = client.get("/docs")
    assert res.status_code == 200

def test_no_logueado():
    res = client.get("/user")
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing or invalid Authorization header"

