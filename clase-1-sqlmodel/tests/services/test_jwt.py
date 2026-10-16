from services.jwt import JWTService


def test_init():
    jwt_service = JWTService("my-secret")
    assert jwt_service.algorithm == "HS256"
    assert jwt_service.expire_minutes == 30