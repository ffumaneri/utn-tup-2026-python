from typing import Annotated, Sequence

from fastapi import APIRouter, HTTPException, Query

from api.model.users import CreateUserRequest, CreateUserResponse, DeleteUserResponse, GetUserResponseWithCountry, GetUsersResponse
from dependencies import UserServiceDep
from model.users import User, UserDB

router = APIRouter()

@router.post("/user", response_model=CreateUserResponse)
def create_user(req: CreateUserRequest, service: UserServiceDep) -> User:
    user = User(name=req.name, age=req.age, country_id=req.country_id)
    return service.create_user(user)


@router.get("/user", response_model=Sequence[GetUsersResponse])
def get_users_endpoint(
    service: UserServiceDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
)-> Sequence[User]:
    return service.get_users(offset, limit)
    


@router.get("/user/{user_id}", response_model=GetUserResponseWithCountry)
def get_user_by_id(user_id: int, service: UserServiceDep) -> UserDB:
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/user/search/{name}")
def search_user(name: str, service: UserServiceDep) -> Sequence[UserDB]:
    return service.search_users(name)


@router.get("/user_mayores")
def search_mayores(service: UserServiceDep)-> Sequence[UserDB]:
    return service.search_mayores()

@router.delete("/user/{user_id}", response_model=DeleteUserResponse)
def delete_user(user_id: int, service: UserServiceDep) -> DeleteUserResponse:
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    service.delete_user(user_id)
    return DeleteUserResponse(msg='Usuario borrado con éxito')

@router.patch("/user/{user_id}", response_model=CreateUserResponse)
def update_user(user_id: int, req: CreateUserRequest, service: UserServiceDep) -> UserDB | None:
    user = User(name=req.name, age=req.age, country_id=req.country_id)
    res = service.update_user(user_id, user)
    if res:
        return res

    raise HTTPException(status_code=404, detail="User not found")
