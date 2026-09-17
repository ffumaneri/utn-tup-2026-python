from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import col, select

from api.model.users import CreateUserRequest, CreateUserResponse, GetUserResponseWithCountry, GetUsersResponse
from model.users import User, UserDB
from repositories.database import SessionDep
from services.users import UserService

router = APIRouter()

UserServiceDep = Annotated[UserService, Depends(UserService)]

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
def get_user_by_id(user_id: int, session: SessionDep) -> UserDB:
    user = session.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/user/search/{name}")
def search_user(name: str, session: SessionDep) -> Sequence[UserDB]:
    statement = select(UserDB).where(col(User.name).like("%{}%".format(name)))
    result = session.exec(statement)
    return result.all()


@router.get("/user_mayores")
def search_mayores(session: SessionDep)-> Sequence[UserDB]:
    # TODO: users.age >= 18
    statement = select(UserDB).where(UserDB.age >= 18)
    result = session.exec(statement)
    return result.all()