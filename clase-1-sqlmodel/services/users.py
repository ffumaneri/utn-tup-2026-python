from typing import Annotated, Sequence

from fastapi import Query

from data.database import SessionDep
from data.users import fetch_users
from model.users import User


def get_users(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
)-> Sequence[User]:
    return fetch_users(session, offset, limit)