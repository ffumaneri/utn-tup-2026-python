from typing import Annotated, Sequence

from fastapi import Depends, Query

from model.users import User
from repositories.users import UserRepository

UserRepositoryDep = Annotated[UserRepository, Depends(UserRepository)]


class UserService:
    def __init__(self, repo: UserRepositoryDep):
        self.repo = repo

    def get_users(
        self,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
    )-> Sequence[User]:
        return self.repo.fetch_users(offset, limit)

    def create_user(self, user: User) -> User:
        return self.repo.create_user(user)
