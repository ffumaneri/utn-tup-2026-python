from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F", bound=Callable)


def protected(func: F) -> F:
    # Marca el endpoint como protegido; JWTAuthMW lo lee para exigir el token.
    func.__protected__ = True  # type: ignore[attr-defined]
    return func
