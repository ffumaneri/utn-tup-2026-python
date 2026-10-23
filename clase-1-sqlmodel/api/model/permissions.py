from sqlmodel import SQLModel


class CreatePermissionRequest(SQLModel):
    name: str
    description: str | None = None


class CreatePermissionResponse(SQLModel):
    id: int


class GetPermissionsResponse(SQLModel):
    id: int
    name: str


class GetPermissionResponse(GetPermissionsResponse):
    description: str | None = None


class DeletePermissionResponse(SQLModel):
    msg: str
