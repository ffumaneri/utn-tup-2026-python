from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Annotated

from fastapi import Query

from dependencies import PermissionRepositoryDep
from model.roles import Permission, PermissionBase


class PermissionServiceInterface(ABC):
    @abstractmethod
    def get_permissions(self, offset: int, limit: int) -> Sequence[Permission]: ...

    @abstractmethod
    def create_permission(self, permission: PermissionBase) -> Permission: ...

    @abstractmethod
    def get_permission_by_id(self, permission_id: int) -> Permission | None: ...

    @abstractmethod
    def get_permission_by_name(self, name: str) -> Permission | None: ...

    @abstractmethod
    def delete_permission(self, permission_id: int): ...

    @abstractmethod
    def update_permission(self, permission_id: int, permission: PermissionBase) -> Permission | None: ...


class PermissionService(PermissionServiceInterface):
    def __init__(self, repo: PermissionRepositoryDep):
        self.repo = repo

    def get_permissions(self, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> Sequence[Permission]:
        return self.repo.fetch_permissions(offset, limit)

    def create_permission(self, permission: PermissionBase) -> Permission:
        return self.repo.create_permission(permission)

    def get_permission_by_id(self, permission_id: int) -> Permission | None:
        return self.repo.get_by_id(permission_id)

    def get_permission_by_name(self, name: str) -> Permission | None:
        return self.repo.get_by_name(name)

    def delete_permission(self, permission_id: int):
        self.repo.delete_permission(permission_id)

    def update_permission(self, permission_id: int, permission: PermissionBase) -> Permission | None:
        return self.repo.update_permission(permission_id, permission)
