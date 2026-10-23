from sqlmodel import SQLModel

from api.model.permissions import GetPermissionResponse


class CreateRoleRequest(SQLModel):
    name: str
    description: str | None = None


class CreateRoleResponse(SQLModel):
    id: int


class RoleResponse(SQLModel):
    id: int
    name: str


class GetRolesResponse(SQLModel):
    id: int
    name: str


class GetRoleResponseWithPermissions(GetRolesResponse):
    description: str | None = None
    permissions: list[GetPermissionResponse] = []


class DeleteRoleResponse(SQLModel):
    msg: str
