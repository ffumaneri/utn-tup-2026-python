from fastapi import HTTPException, Request

from dependencies import get_jwt_service


class JWTAuthMW:
    """Se registra como dependencia global: corre después del ruteo, cuando ya se conoce el endpoint."""

    def __init__(self):
        self.jwt_service = get_jwt_service()

    def _is_protected(self, request: Request) -> bool:
        # El endpoint ya fue resuelto por el router; se lee la marca que deja @protected.
        route = request.scope.get("route")
        return getattr(getattr(route, "endpoint", None), "__protected__", False)

    async def check_jwt(self, request: Request) -> None:
        if not self._is_protected(request):
            return

        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        payload = self.jwt_service.decode_token(authorization.removeprefix("Bearer "))
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        request.state.jwt_payload = payload
