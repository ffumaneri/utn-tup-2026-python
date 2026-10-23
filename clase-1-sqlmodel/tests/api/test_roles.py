import pytest


def test_get_roles_ok(client, auth_headers):
    res = client.get("/role", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_role_by_id_ok(client, auth_headers):
    res = client.get("/role/1", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "ADMIN"
    assert [p["name"] for p in res.json()["permissions"]] == [
        "write_users", "read_users", "delete_users", "update_users"
    ]


def test_regular_role_only_reads_users(client, auth_headers):
    res = client.get("/role/2", headers=auth_headers)
    assert res.json()["name"] == "REGULAR"
    assert [p["name"] for p in res.json()["permissions"]] == ["read_users"]


def test_get_role_by_id_fail(client, auth_headers):
    res = client.get("/role/120", headers=auth_headers)
    assert res.status_code == 404


def test_create_role_ok(client, auth_headers):
    res = client.post("/role", json={"name": "editor", "description": "Edits"}, headers=auth_headers)
    assert res.status_code == 201
    assert client.get(f"/role/{res.json()['id']}", headers=auth_headers).json()["name"] == "editor"


def test_create_role_duplicate(client, auth_headers):
    res = client.post("/role", json={"name": "ADMIN"}, headers=auth_headers)
    assert res.status_code == 409


def test_update_role_ok(client, auth_headers):
    res = client.patch("/role/2", json={"name": "visitor", "description": "Visits"}, headers=auth_headers)
    assert res.status_code == 200
    assert client.get("/role/2", headers=auth_headers).json()["name"] == "visitor"


def test_update_role_duplicate(client, auth_headers):
    res = client.patch("/role/2", json={"name": "ADMIN"}, headers=auth_headers)
    assert res.status_code == 409


def test_update_role_fail(client, auth_headers):
    res = client.patch("/role/120", json={"name": "x"}, headers=auth_headers)
    assert res.status_code == 404


def test_delete_role_ok(client, auth_headers):
    assert client.delete("/role/2", headers=auth_headers).status_code == 200
    assert client.get("/role/2", headers=auth_headers).status_code == 404


def test_delete_role_fail(client, auth_headers):
    assert client.delete("/role/120", headers=auth_headers).status_code == 404


def test_add_permission_to_role(client, auth_headers):
    res = client.post("/role/2/permission/1", headers=auth_headers)
    assert res.status_code == 200
    assert [p["name"] for p in res.json()["permissions"]] == ["write_users", "read_users"]


def test_add_permission_is_idempotent(client, auth_headers):
    res = client.post("/role/1/permission/1", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()["permissions"]) == 4


def test_add_permission_not_found(client, auth_headers):
    assert client.post("/role/120/permission/1", headers=auth_headers).status_code == 404
    assert client.post("/role/1/permission/120", headers=auth_headers).status_code == 404


def test_remove_permission_from_role(client, auth_headers):
    res = client.delete("/role/2/permission/2", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["permissions"] == []


def test_remove_permission_not_found(client, auth_headers):
    assert client.delete("/role/120/permission/1", headers=auth_headers).status_code == 404
    assert client.delete("/role/1/permission/120", headers=auth_headers).status_code == 404


@pytest.mark.parametrize(
    "method, path",
    [("get", "/role"), ("get", "/role/1"), ("post", "/role"), ("delete", "/role/1"), ("post", "/role/1/permission/1")],
)
def test_roles_protegidos(client, method, path):
    res = getattr(client, method)(path)
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing or invalid Authorization header"


def test_get_role_users(client, auth_headers):
    assert [u["id"] for u in client.get("/role/1/user", headers=auth_headers).json()] == [1]
    assert [u["id"] for u in client.get("/role/2/user", headers=auth_headers).json()] == [2, 3]


def test_get_role_users_not_found(client, auth_headers):
    assert client.get("/role/120/user", headers=auth_headers).status_code == 404


def test_delete_role_removes_user_link(client, auth_headers):
    assert client.delete("/role/2", headers=auth_headers).status_code == 200
    assert client.get("/user/2", headers=auth_headers).json()["roles"] == []
