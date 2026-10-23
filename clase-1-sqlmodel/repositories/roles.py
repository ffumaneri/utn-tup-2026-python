from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from sqlmodel import col, select

from dependencies import SessionDep
from model.roles import Permission, Role, RoleBase


class RoleRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    def fetch_roles(self, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> Sequence[Role]:
        statement = select(Role).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def create_role(self, role_base: RoleBase) -> Role:
        role = Role(name=role_base.name, description=role_base.description)
        self.session.add(role)
        self.session.commit()
        self.session.refresh(role)
        return role

    def get_by_id(self, role_id: int) -> Role | None:
        return self.session.get(Role, role_id)

    def get_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(col(Role.name) == name)
        return self.session.exec(statement).first()

    def delete_role(self, role_id: int):
        role = self.session.get(Role, role_id)
        if role:
            self.session.delete(role)
            self.session.commit()

    def update_role(self, role_id: int, role: RoleBase) -> Role | None:
        role_db = self.session.get(Role, role_id)
        if role_db:
            role_db.name = role.name
            role_db.description = role.description
            self.session.add(role_db)
            self.session.commit()
            self.session.refresh(role_db)
        return role_db

    def add_permission(self, role: Role, permission: Permission) -> Role:
        if permission not in role.permissions:
            role.permissions.append(permission)
            self.session.add(role)
            self.session.commit()
            self.session.refresh(role)
        return role

    def remove_permission(self, role: Role, permission: Permission) -> Role:
        if permission in role.permissions:
            role.permissions.remove(permission)
            self.session.add(role)
            self.session.commit()
            self.session.refresh(role)
        return role
