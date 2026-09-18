from typing import Annotated, Sequence

from fastapi import Depends, Query
from sqlmodel import col, select

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

    def get_by_id(self, user_id: int) -> UserDB | None:
        return self.session.get(UserDB, user_id)

    def search_by_name(self, name: str) -> Sequence[UserDB]:
        statement = select(UserDB).where(col(UserDB.name).like("%{}%".format(name)))
        result = self.session.exec(statement)
        return result.all()

    def fetch_adults(self) -> Sequence[UserDB]:
        statement = select(UserDB).where(UserDB.age >= 18)
        result = self.session.exec(statement)
        return result.all()

    def delete_user(self, user_id: int):
        user = self.session.get(UserDB, user_id)
        self.session.delete(user)
        self.session.commit()

    def update_user(self, user_id: int, user: User) -> UserDB | None:
        userDb = self.session.get(UserDB, user_id)
        if userDb:
            userDb.age = user.age
            userDb.name = user.name
            userDb.country_id = user.country_id
            self.session.add(userDb)
            self.session.commit()
            self.session.refresh(userDb)
        return userDb


UserRepositoryDep = Annotated[UserRepository, Depends(UserRepository)]
