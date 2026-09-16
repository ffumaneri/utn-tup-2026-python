from typing import Annotated, Sequence

from fastapi import Query
from sqlmodel import select

from model.users import User
from repositories.database import SessionDep


class UserRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    def fetch_users(
        self,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
    )-> Sequence[User]:
        statement = select(User).offset(offset).limit(limit)
        result = self.session.exec(statement)
        users = result.all()
        return users