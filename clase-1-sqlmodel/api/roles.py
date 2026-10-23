from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from api.middlewares.protected import protected
from api.model.roles import (
    CreateRoleRequest,
    CreateRoleResponse,
    DeleteRoleResponse,
    GetRoleResponseWithPermissions,
    GetRolesResponse,
)
from api.model.users import GetUsersResponse
from dependencies import PermissionServiceDep, RoleServiceDep
from model.roles import Role, RoleBase
from model.users import UserDB

router = APIRouter(tags=["Roles"], dependencies=[Depends(HTTPBearer())])


@router.post("/role", response_model=CreateRoleResponse, status_code=201)
@protected
def create_role(req: CreateRoleRequest, service: RoleServiceDep) -> Role:
    if service.get_role_by_name(req.name):
        raise HTTPException(status_code=409, detail="Role already exists")
    return service.create_role(RoleBase(name=req.name, description=req.description))


@router.get("/role", response_model=Sequence[GetRolesResponse])
@protected
def get_roles(service: RoleServiceDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> Sequence[Role]:
    return service.get_roles(offset, limit)


@router.get("/role/{role_id}", response_model=GetRoleResponseWithPermissions)
@protected
def get_role_by_id(role_id: int, service: RoleServiceDep) -> Role:
    role = service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.patch("/role/{role_id}", response_model=CreateRoleResponse)
@protected
def update_role(role_id: int, req: CreateRoleRequest, service: RoleServiceDep) -> Role:
    existing = service.get_role_by_name(req.name)
    if existing and existing.id != role_id:
        raise HTTPException(status_code=409, detail="Role already exists")
    res = service.update_role(role_id, RoleBase(name=req.name, description=req.description))
    if not res:
        raise HTTPException(status_code=404, detail="Role not found")
    return res


@router.delete("/role/{role_id}", response_model=DeleteRoleResponse)
@protected
def delete_role(role_id: int, service: RoleServiceDep) -> DeleteRoleResponse:
    if not service.get_role_by_id(role_id):
        raise HTTPException(status_code=404, detail="Role not found")
    service.delete_role(role_id)
    return DeleteRoleResponse(msg="Rol borrado con éxito")


@router.post("/role/{role_id}/permission/{permission_id}", response_model=GetRoleResponseWithPermissions)
@protected
def add_permission_to_role(
    role_id: int, permission_id: int, service: RoleServiceDep, permission_service: PermissionServiceDep
) -> Role:
    role = service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permission = permission_service.get_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return service.add_permission(role, permission)


@router.delete("/role/{role_id}/permission/{permission_id}", response_model=GetRoleResponseWithPermissions)
@protected
def remove_permission_from_role(
    role_id: int, permission_id: int, service: RoleServiceDep, permission_service: PermissionServiceDep
) -> Role:
    role = service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permission = permission_service.get_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return service.remove_permission(role, permission)


@router.get("/role/{role_id}/user", response_model=Sequence[GetUsersResponse])
@protected
def get_role_users(role_id: int, service: RoleServiceDep) -> Sequence[UserDB]:
    role = service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role.users
