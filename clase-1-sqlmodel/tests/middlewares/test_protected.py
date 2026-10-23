from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.middlewares.auth import JWTAuthMW
from api.middlewares.protected import protected


def test_protected_returns_same_function_and_flags_it():
    def endpoint():
        return 1

    assert protected(endpoint) is endpoint
    assert endpoint.__protected__ is True  # type: ignore[attr-defined]


def _build_app() -> FastAPI:
    app = FastAPI(dependencies=[Depends(JWTAuthMW().check_jwt)])

    @app.get("/open")
    def open_endpoint():
        return {"ok": True}

    @app.get("/closed")
    @protected
    def closed_endpoint():
        return {"ok": True}

    return app


def test_unannotated_endpoint_is_public():
    assert TestClient(_build_app()).get("/open").status_code == 200


def test_annotated_endpoint_requires_token():
    res = TestClient(_build_app()).get("/closed")
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing or invalid Authorization header"


def test_unknown_path_falls_through_to_404():
    assert TestClient(_build_app()).get("/nope").status_code == 404


def test_login_stays_public(client):
    res = client.post("/login", json={"email": "x@email.com", "password": "bad"})
    assert res.status_code != 401 or res.json()["detail"] != "Missing or invalid Authorization header"
