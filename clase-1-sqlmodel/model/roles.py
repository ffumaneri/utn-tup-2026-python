from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from model.users import UserDB

ADMIN_ROLE = "ADMIN"
REGULAR_ROLE = "REGULAR"


# Tabla intermedia Role <-> Permission (muchos a muchos)
class RolePermission(SQLModel, table=True):
    role_id: int | None = Field(default=None, foreign_key="role.id", primary_key=True)
    permission_id: int | None = Field(default=None, foreign_key="permission.id", primary_key=True)


# Tabla intermedia User <-> Role (no modifica la tabla de usuarios)
class UserRole(SQLModel, table=True):
    user_id: int | None = Field(default=None, foreign_key="userdb.id", primary_key=True)
    role_id: int | None = Field(default=None, foreign_key="role.id", primary_key=True)


# Nivel de negocio
class RoleBase(SQLModel):
    name: str = Field(unique=True, index=True)
    description: str | None = None


class PermissionBase(SQLModel):
    name: str = Field(unique=True, index=True)
    description: str | None = None


# Nivel de base de datos
class Role(RoleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    permissions: list["Permission"] = Relationship(back_populates="roles", link_model=RolePermission)
    users: list["UserDB"] = Relationship(back_populates="roles", link_model=UserRole)


class Permission(PermissionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    roles: list[Role] = Relationship(back_populates="permissions", link_model=RolePermission)
