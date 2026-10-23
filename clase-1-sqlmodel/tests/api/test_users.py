# get users
import pytest


def test_get_user_ok(client, auth_headers):
    res = client.get("/user", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 3


# get user by id
def test_get_user_by_id_ok(client, auth_headers):
    res = client.get("/user/1", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == 1
    assert res.json()["email"] == "mgomez@email.com"

def test_get_user_by_id_fail(client, auth_headers):
    res = client.get("/user/120", headers=auth_headers)
    assert res.status_code == 404

# no logueados
@pytest.mark.parametrize(
        "method, path",
        [
            ("get", "/user"),
            ("get", "/user/1"),
            ("get", "/user/search/ma")
        ],
)
def test_protegidos(client, method, path):
    res = getattr(client, method)(path)
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing or invalid Authorization header"


def test_get_user_returns_roles(client, auth_headers):
    assert [r["name"] for r in client.get("/user/1", headers=auth_headers).json()["roles"]] == ["ADMIN"]
    assert [r["name"] for r in client.get("/user/2", headers=auth_headers).json()["roles"]] == ["REGULAR"]


def test_created_user_is_regular_by_default(client, auth_headers):
    body = {"name": "Nuevo", "age": 30, "country_id": 1, "email": "nuevo@email.com", "password": "1234"}
    res = client.post("/user", json=body, headers=auth_headers)
    assert res.status_code == 200
    roles = client.get(f"/user/{res.json()['id']}", headers=auth_headers).json()["roles"]
    assert [r["name"] for r in roles] == ["REGULAR"]


def test_add_role_to_user(client, auth_headers):
    res = client.post("/user/2/role/1", headers=auth_headers)
    assert res.status_code == 200
    assert sorted(r["name"] for r in res.json()["roles"]) == ["ADMIN", "REGULAR"]


def test_add_role_to_user_is_idempotent(client, auth_headers):
    res = client.post("/user/2/role/2", headers=auth_headers)
    assert [r["name"] for r in res.json()["roles"]] == ["REGULAR"]


def test_remove_role_from_user(client, auth_headers):
    res = client.delete("/user/2/role/2", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["roles"] == []


def test_user_role_not_found(client, auth_headers):
    assert client.post("/user/120/role/1", headers=auth_headers).status_code == 404
    assert client.post("/user/1/role/120", headers=auth_headers).status_code == 404
    assert client.delete("/user/120/role/1", headers=auth_headers).status_code == 404
    assert client.delete("/user/1/role/120", headers=auth_headers).status_code == 404


def test_delete_user_removes_role_link(client, auth_headers):
    assert client.delete("/user/3", headers=auth_headers).status_code == 200
    assert [u["id"] for u in client.get("/role/2/user", headers=auth_headers).json()] == [2]


@pytest.mark.parametrize("method, path", [("post", "/user/1/role/1"), ("delete", "/user/1/role/1")])
def test_user_roles_protegidos(client, method, path):
    assert getattr(client, method)(path).status_code == 401
