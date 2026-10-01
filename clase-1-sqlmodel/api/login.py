from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from api.model.login import Login, LoginResponse
from services.jwt import JWTService
from services.login import LoginService

router = APIRouter(tags=["Auth"])
LoginServiceDep = Annotated[LoginService, Depends(LoginService)]


@router.post("/login", response_model=LoginResponse)
def login(req: Login, service: LoginServiceDep) -> LoginResponse:
    valid = service.login(req.email, req.password)
    if not valid:
        raise HTTPException(status_code=401, detail="User/password incorrect")
    jwt_service = JWTService("mi-secret")
    
    return LoginResponse(msg="ok", token=jwt_service.create_access_token({"sub": req.email}))
    
