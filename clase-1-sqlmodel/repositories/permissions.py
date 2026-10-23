from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from sqlmodel import col, select

from dependencies import SessionDep
from model.roles import Permission, PermissionBase


class PermissionRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    def fetch_permissions(self, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> Sequence[Permission]:
        statement = select(Permission).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def create_permission(self, permission_base: PermissionBase) -> Permission:
        permission = Permission(name=permission_base.name, description=permission_base.description)
        self.session.add(permission)
        self.session.commit()
        self.session.refresh(permission)
        return permission

    def get_by_id(self, permission_id: int) -> Permission | None:
        return self.session.get(Permission, permission_id)

    def get_by_name(self, name: str) -> Permission | None:
        statement = select(Permission).where(col(Permission.name) == name)
        return self.session.exec(statement).first()

    def delete_permission(self, permission_id: int):
        permission = self.session.get(Permission, permission_id)
        if permission:
            self.session.delete(permission)
            self.session.commit()

    def update_permission(self, permission_id: int, permission: PermissionBase) -> Permission | None:
        permission_db = self.session.get(Permission, permission_id)
        if permission_db:
            permission_db.name = permission.name
            permission_db.description = permission.description
            self.session.add(permission_db)
            self.session.commit()
            self.session.refresh(permission_db)
        return permission_db
