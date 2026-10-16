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
