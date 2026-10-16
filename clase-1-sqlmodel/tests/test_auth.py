from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_login_ok():
    res = client.post("/login", json={"email": "mgomez@email.com","password": "123"})
    assert res.status_code == 200
    assert res.json()["msg"] == "ok"
    assert res.json()["token"]

def test_login_wrong_pwd():
    res = client.post("/login", json={"email": "mgomez@email.com","password": "incorrecta"})
    assert res.status_code == 401
    assert res.json()["detail"] == "User/password incorrect"

def test_login_wrong_user():
    res = client.post("/login", json={"email": "incorrect@email.com","password": "123"})
    assert res.status_code == 401
    assert res.json()["detail"] == "User/password incorrect"

def test_login_wrong_request():
    res = client.post("/login", json={"prueba": "incorrect@email.com"})
    assert res.status_code == 422
