from fastapi import Request
from fastapi.responses import JSONResponse

from dependencies import get_jwt_service


class JWTAuthMW:
    def __init__(self):
        self.jwt_service = get_jwt_service()

    def _is_protected(self, path: str) -> bool:
        return path == "/user" or path.startswith("/user/") or path == "/user_mayores"

    async def check_jwt(self, request: Request, call_next):
        if not self._is_protected(request.url.path):
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        payload = self.jwt_service.decode_token(authorization.removeprefix("Bearer "))
        if payload is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        request.state.jwt_payload = payload
        return await call_next(request)
