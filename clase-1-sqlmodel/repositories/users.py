from typing import Annotated, Sequence

from fastapi import Query
from sqlmodel import select

from model.users import User, UserDB
from repositories.database import SessionDep


class UserRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    def fetch_users(
        self,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
    )-> Sequence[UserDB]:
        statement = select(UserDB).offset(offset).limit(limit)
        result = self.session.exec(statement)
        users = result.all()
        return users

    def create_user(self, userBase: User) -> UserDB:
        user = UserDB(name=userBase.name, age=userBase.age, country_id=userBase.country_id)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user