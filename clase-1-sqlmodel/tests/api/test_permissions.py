import pytest


def test_get_permissions_ok(client, auth_headers):
    res = client.get("/permission", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 4


def test_get_permission_by_id_ok(client, auth_headers):
    res = client.get("/permission/1", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "write_users"
    assert res.json()["description"] is None


def test_get_permission_by_id_fail(client, auth_headers):
    assert client.get("/permission/120", headers=auth_headers).status_code == 404


def test_create_permission_ok(client, auth_headers):
    res = client.post("/permission", json={"name": "export", "description": "Exports"}, headers=auth_headers)
    assert res.status_code == 201
    assert client.get(f"/permission/{res.json()['id']}", headers=auth_headers).json()["name"] == "export"


def test_create_permission_duplicate(client, auth_headers):
    res = client.post("/permission", json={"name": "read_users"}, headers=auth_headers)
    assert res.status_code == 409


def test_update_permission_ok(client, auth_headers):
    res = client.patch("/permission/2", json={"name": "edit", "description": "Edits"}, headers=auth_headers)
    assert res.status_code == 200
    assert client.get("/permission/2", headers=auth_headers).json()["name"] == "edit"


def test_update_permission_same_name_ok(client, auth_headers):
    res = client.patch("/permission/1", json={"name": "write_users", "description": "New"}, headers=auth_headers)
    assert res.status_code == 200


def test_update_permission_duplicate(client, auth_headers):
    res = client.patch("/permission/2", json={"name": "write_users"}, headers=auth_headers)
    assert res.status_code == 409


def test_update_permission_fail(client, auth_headers):
    assert client.patch("/permission/120", json={"name": "x"}, headers=auth_headers).status_code == 404


def test_delete_permission_ok(client, auth_headers):
    assert client.delete("/permission/3", headers=auth_headers).status_code == 200
    assert client.get("/permission/3", headers=auth_headers).status_code == 404


def test_delete_permission_fail(client, auth_headers):
    assert client.delete("/permission/120", headers=auth_headers).status_code == 404


@pytest.mark.parametrize(
    "method, path",
    [("get", "/permission"), ("get", "/permission/1"), ("post", "/permission"), ("delete", "/permission/1")],
)
def test_permissions_protegidos(client, method, path):
    res = getattr(client, method)(path)
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing or invalid Authorization header"
