from abc import ABC, abstractmethod
from typing import Annotated, Sequence

from fastapi import Query

from dependencies import UserRepositoryDep
from model.users import User, UserDB


class UserServiceInterface(ABC):
    @abstractmethod
    def get_users(self, offset: int, limit: int) -> Sequence[User]:
        ...

    @abstractmethod
    def create_user(self, user: User) -> User:
        ...

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> UserDB | None:
        ...

    @abstractmethod
    def search_users(self, name: str) -> Sequence[UserDB]:
        ...

    @abstractmethod
    def search_mayores(self) -> Sequence[UserDB]:
        ...


class UserService(UserServiceInterface):
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

    def get_user_by_id(self, user_id: int) -> UserDB | None:
        return self.repo.get_by_id(user_id)

    def search_users(self, name: str) -> Sequence[UserDB]:
        return self.repo.search_by_name(name)

    def search_mayores(self) -> Sequence[UserDB]:
        return self.repo.fetch_adults()
