from typing import Annotated, Sequence

from fastapi import Query
from sqlmodel import select

from data.database import SessionDep
from model.users import User


def fetch_users(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
)-> Sequence[User]:
    statement = select(User).offset(offset).limit(limit)
    result = session.exec(statement)
    users = result.all()
    return users