from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Annotated

from fastapi import Query

from dependencies import RoleRepositoryDep
from model.roles import Permission, Role, RoleBase


class RoleServiceInterface(ABC):
    @abstractmethod
    def get_roles(self, offset: int, limit: int) -> Sequence[Role]: ...

    @abstractmethod
    def create_role(self, role: RoleBase) -> Role: ...

    @abstractmethod
    def get_role_by_id(self, role_id: int) -> Role | None: ...

    @abstractmethod
    def get_role_by_name(self, name: str) -> Role | None: ...

    @abstractmethod
    def delete_role(self, role_id: int): ...

    @abstractmethod
    def update_role(self, role_id: int, role: RoleBase) -> Role | None: ...

    @abstractmethod
    def add_permission(self, role: Role, permission: Permission) -> Role: ...

    @abstractmethod
    def remove_permission(self, role: Role, permission: Permission) -> Role: ...


class RoleService(RoleServiceInterface):
    def __init__(self, repo: RoleRepositoryDep):
        self.repo = repo

    def get_roles(self, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> Sequence[Role]:
        return self.repo.fetch_roles(offset, limit)

    def create_role(self, role: RoleBase) -> Role:
        return self.repo.create_role(role)

    def get_role_by_id(self, role_id: int) -> Role | None:
        return self.repo.get_by_id(role_id)

    def get_role_by_name(self, name: str) -> Role | None:
        return self.repo.get_by_name(name)

    def delete_role(self, role_id: int):
        self.repo.delete_role(role_id)

    def update_role(self, role_id: int, role: RoleBase) -> Role | None:
        return self.repo.update_role(role_id, role)

    def add_permission(self, role: Role, permission: Permission) -> Role:
        return self.repo.add_permission(role, permission)

    def remove_permission(self, role: Role, permission: Permission) -> Role:
        return self.repo.remove_permission(role, permission)
