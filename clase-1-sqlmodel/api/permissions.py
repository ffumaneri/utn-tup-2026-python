from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from api.middlewares.protected import protected
from api.model.permissions import (
    CreatePermissionRequest,
    CreatePermissionResponse,
    DeletePermissionResponse,
    GetPermissionResponse,
    GetPermissionsResponse,
)
from dependencies import PermissionServiceDep
from model.roles import Permission, PermissionBase

router = APIRouter(tags=["Permissions"], dependencies=[Depends(HTTPBearer())])


@router.post("/permission", response_model=CreatePermissionResponse, status_code=201)
@protected
def create_permission(req: CreatePermissionRequest, service: PermissionServiceDep) -> Permission:
    if service.get_permission_by_name(req.name):
        raise HTTPException(status_code=409, detail="Permission already exists")
    return service.create_permission(PermissionBase(name=req.name, description=req.description))


@router.get("/permission", response_model=Sequence[GetPermissionsResponse])
@protected
def get_permissions(
    service: PermissionServiceDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> Sequence[Permission]:
    return service.get_permissions(offset, limit)


@router.get("/permission/{permission_id}", response_model=GetPermissionResponse)
@protected
def get_permission_by_id(permission_id: int, service: PermissionServiceDep) -> Permission:
    permission = service.get_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission


@router.patch("/permission/{permission_id}", response_model=CreatePermissionResponse)
@protected
def update_permission(permission_id: int, req: CreatePermissionRequest, service: PermissionServiceDep) -> Permission:
    existing = service.get_permission_by_name(req.name)
    if existing and existing.id != permission_id:
        raise HTTPException(status_code=409, detail="Permission already exists")
    res = service.update_permission(permission_id, PermissionBase(name=req.name, description=req.description))
    if not res:
        raise HTTPException(status_code=404, detail="Permission not found")
    return res


@router.delete("/permission/{permission_id}", response_model=DeletePermissionResponse)
@protected
def delete_permission(permission_id: int, service: PermissionServiceDep) -> DeletePermissionResponse:
    if not service.get_permission_by_id(permission_id):
        raise HTTPException(status_code=404, detail="Permission not found")
    service.delete_permission(permission_id)
    return DeletePermissionResponse(msg="Permiso borrado con éxito")
