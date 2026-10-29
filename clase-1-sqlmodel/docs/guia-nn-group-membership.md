# Guía: N-N con atributos en SQLModel (User ↔ Group)

## 0. Qué vamos a construir
Hoy `clase-1-sqlmodel` tiene N-N con **tabla intermedia pura** (`UserRole`, `RolePermission`, usando `link_model`). Ahora agregamos **Grupos** de usuarios donde la relación tiene datos propios:

| Tabla | Campos |
|---|---|
| `group` | id, name (único), description |
| `membership` | user_id (PK, FK), group_id (PK, FK), **joined_at**, **is_leader** |

Cuando la relación necesita columnas extra, `link_model` no alcanza: se modela la tabla intermedia como una **entidad más** (*association object*) y se navega `User → Membership → Group`.

Reglas de negocio:
1. Nombre de grupo único (409).
2. Un usuario no puede unirse dos veces al mismo grupo (409).
3. Solo un líder por grupo; solo un miembro puede ser líder (409 si no lo es).
4. Al borrar un grupo se borran sus memberships (los usuarios no se tocan).

Orden de trabajo (cada paso termina con algo que se puede probar): modelo → repositorio → servicio → dependencias → API → router → tests.

---

## Paso 1 — Modelo: `model/groups.py` (archivo nuevo)

```python
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from model.users import UserDB


# Nivel de negocio
class GroupBase(SQLModel):
    name: str = Field(unique=True, index=True)
    description: str | None = None


# Tabla intermedia con datos propios: es una entidad, no un link_model
class Membership(SQLModel, table=True):
    user_id: int | None = Field(default=None, foreign_key="userdb.id", primary_key=True)
    group_id: int | None = Field(default=None, foreign_key="group.id", primary_key=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_leader: bool = False

    user: "UserDB" = Relationship(back_populates="memberships")
    group: "Group" = Relationship(back_populates="memberships")


# Nivel de base de datos
class Group(GroupBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    memberships: list[Membership] = Relationship(back_populates="group", cascade_delete=True)
```

Puntos a explicar en clase:
- La **PK compuesta** (`user_id` + `group_id`) impide a nivel de base de datos que el mismo usuario esté dos veces en el mismo grupo.
- `Membership` tiene una relación **N-1 con User** y otra **N-1 con Group**. Un N-N con atributos son dos 1-N.
- `cascade_delete=True`: SQLite no cascadea solo; así SQLModel borra las memberships al borrar el grupo.
- Mismo truco que `model/roles.py`: `UserDB` se importa solo bajo `TYPE_CHECKING` para evitar el import circular.

## Paso 2 — Conectar `UserDB`: `model/users.py`

Agregar el import y la relación:

```python
from model.groups import Membership   # junto a: from model.roles import Role, UserRole
```

```python
class UserDB(User, table=True):
    id: int | None = Field(default=None, primary_key=True)
    country: Country | None = Relationship(back_populates="users")
    roles: list[Role] = Relationship(back_populates="users", link_model=UserRole)
    memberships: list[Membership] = Relationship(back_populates="user", cascade_delete=True)  # nuevo
```

`cascade_delete=True` también acá: si se borra un usuario, se borran sus memberships (si no, queda una FK huérfana).

> No hay migración: `create_db_and_tables()` en `repositories/database.py` ejecuta `SQLModel.metadata.create_all`, que crea las tablas nuevas sin tocar las existentes. Las tablas deben estar registradas antes de ese llamado; por eso `main.py` importa el router (Paso 6), que importa el modelo.

**Chequeo rápido:** `.venv/bin/python -c "import main"` no debe fallar (si falla por mappers, falta algún import del modelo).

---

## Paso 3 — Repositorio: `repositories/groups.py` (nuevo)

Mismo estilo que `repositories/roles.py`: recibe la sesión por `SessionDep`.

```python
from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from sqlmodel import col, select

from dependencies import SessionDep
from model.groups import Group, GroupBase, Membership


class GroupRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    # --- CRUD de grupos ---
    def fetch_groups(self, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> Sequence[Group]:
        statement = select(Group).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def create_group(self, group_base: GroupBase) -> Group:
        group = Group(name=group_base.name, description=group_base.description)
        self.session.add(group)
        self.session.commit()
        self.session.refresh(group)
        return group

    def get_by_id(self, group_id: int) -> Group | None:
        return self.session.get(Group, group_id)

    def get_by_name(self, name: str) -> Group | None:
        statement = select(Group).where(col(Group.name) == name)
        return self.session.exec(statement).first()

    def update_group(self, group_id: int, group: GroupBase) -> Group | None:
        group_db = self.session.get(Group, group_id)
        if group_db:
            group_db.name = group.name
            group_db.description = group.description
            self.session.add(group_db)
            self.session.commit()
            self.session.refresh(group_db)
        return group_db

    def delete_group(self, group_id: int):
        group = self.session.get(Group, group_id)
        if group:
            self.session.delete(group)   # cascade_delete borra las memberships
            self.session.commit()

    # --- Membresías ---
    def get_membership(self, group_id: int, user_id: int) -> Membership | None:
        # El orden de la tupla es el de las columnas PK: (user_id, group_id)
        return self.session.get(Membership, (user_id, group_id))

    def add_member(self, group_id: int, user_id: int) -> Membership:
        membership = Membership(group_id=group_id, user_id=user_id)
        self.session.add(membership)
        self.session.commit()
        self.session.refresh(membership)
        return membership

    def remove_member(self, membership: Membership):
        self.session.delete(membership)
        self.session.commit()

    def set_leader(self, group: Group, user_id: int) -> Group:
        # Un único líder: marcamos al elegido y bajamos a todos los demás.
        for membership in group.memberships:
            membership.is_leader = membership.user_id == user_id
            self.session.add(membership)
        self.session.commit()
        self.session.refresh(group)
        return group
```

Nota: `session.get(Membership, (user_id, group_id))` es la forma de buscar por PK compuesta. Un error común de los alumnos es invertir el orden.

---

## Paso 4 — Servicio: `services/groups.py` (nuevo)

Igual que `services/roles.py`: una interfaz abstracta y la implementación que delega en el repositorio.

```python
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Annotated

from fastapi import Query

from dependencies import GroupRepositoryDep
from model.groups import Group, GroupBase, Membership


class GroupServiceInterface(ABC):
    @abstractmethod
    def get_groups(self, offset: int, limit: int) -> Sequence[Group]: ...

    @abstractmethod
    def create_group(self, group: GroupBase) -> Group: ...

    @abstractmethod
    def get_group_by_id(self, group_id: int) -> Group | None: ...

    @abstractmethod
    def get_group_by_name(self, name: str) -> Group | None: ...

    @abstractmethod
    def update_group(self, group_id: int, group: GroupBase) -> Group | None: ...

    @abstractmethod
    def delete_group(self, group_id: int): ...

    @abstractmethod
    def get_membership(self, group_id: int, user_id: int) -> Membership | None: ...

    @abstractmethod
    def add_member(self, group_id: int, user_id: int) -> Membership: ...

    @abstractmethod
    def remove_member(self, membership: Membership): ...

    @abstractmethod
    def set_leader(self, group: Group, user_id: int) -> Group: ...


class GroupService(GroupServiceInterface):
    def __init__(self, repo: GroupRepositoryDep):
        self.repo = repo

    def get_groups(self, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> Sequence[Group]:
        return self.repo.fetch_groups(offset, limit)

    def create_group(self, group: GroupBase) -> Group:
        return self.repo.create_group(group)

    def get_group_by_id(self, group_id: int) -> Group | None:
        return self.repo.get_by_id(group_id)

    def get_group_by_name(self, name: str) -> Group | None:
        return self.repo.get_by_name(name)

    def update_group(self, group_id: int, group: GroupBase) -> Group | None:
        return self.repo.update_group(group_id, group)

    def delete_group(self, group_id: int):
        self.repo.delete_group(group_id)

    def get_membership(self, group_id: int, user_id: int) -> Membership | None:
        return self.repo.get_membership(group_id, user_id)

    def add_member(self, group_id: int, user_id: int) -> Membership:
        return self.repo.add_member(group_id, user_id)

    def remove_member(self, membership: Membership):
        self.repo.remove_member(membership)

    def set_leader(self, group: Group, user_id: int) -> Group:
        return self.repo.set_leader(group, user_id)
```

## Paso 5 — Inyección de dependencias: `dependencies.py`

Agregar, siguiendo el bloque de roles (los imports van abajo por el ciclo `dependencies` ↔ `repositories`):

```python
from repositories.groups import GroupRepository  # noqa: E402

GroupRepositoryDep = Annotated[GroupRepository, Depends(GroupRepository)]

from services.groups import GroupService, GroupServiceInterface  # noqa: E402

GroupServiceDep = Annotated[GroupServiceInterface, Depends(GroupService)]
```

---

## Paso 6 — Modelos de API: `api/model/groups.py` (nuevo)

```python
from datetime import datetime

from sqlmodel import SQLModel


class CreateGroupRequest(SQLModel):
    name: str
    description: str | None = None


class CreateGroupResponse(SQLModel):
    id: int


class GetGroupsResponse(SQLModel):
    id: int
    name: str


class GetGroupResponse(GetGroupsResponse):
    description: str | None = None


class MemberResponse(SQLModel):
    id: int
    name: str
    joined_at: datetime
    is_leader: bool


class DeleteGroupResponse(SQLModel):
    msg: str
```

`MemberResponse` combina datos del **usuario** (`id`, `name`) con datos de la **relación** (`joined_at`, `is_leader`): ese es el valor del association object.

## Paso 7 — Router: `api/groups.py` (nuevo)

```python
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from api.middlewares.protected import protected
from api.model.groups import (
    CreateGroupRequest,
    CreateGroupResponse,
    DeleteGroupResponse,
    GetGroupResponse,
    GetGroupsResponse,
    MemberResponse,
)
from dependencies import GroupServiceDep, UserServiceDep
from model.groups import Group, GroupBase

router = APIRouter(tags=["Groups"], dependencies=[Depends(HTTPBearer())])


def _members(group: Group) -> list[MemberResponse]:
    return [
        MemberResponse(id=m.user.id, name=m.user.name, joined_at=m.joined_at, is_leader=m.is_leader)
        for m in group.memberships
    ]


@router.post("/group", response_model=CreateGroupResponse, status_code=201)
@protected
def create_group(req: CreateGroupRequest, service: GroupServiceDep) -> Group:
    if service.get_group_by_name(req.name):
        raise HTTPException(status_code=409, detail="Group already exists")
    return service.create_group(GroupBase(name=req.name, description=req.description))


@router.get("/group", response_model=Sequence[GetGroupsResponse])
@protected
def get_groups(
    service: GroupServiceDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> Sequence[Group]:
    return service.get_groups(offset, limit)


@router.get("/group/{group_id}", response_model=GetGroupResponse)
@protected
def get_group_by_id(group_id: int, service: GroupServiceDep) -> Group:
    group = service.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.patch("/group/{group_id}", response_model=CreateGroupResponse)
@protected
def update_group(group_id: int, req: CreateGroupRequest, service: GroupServiceDep) -> Group:
    existing = service.get_group_by_name(req.name)
    if existing and existing.id != group_id:
        raise HTTPException(status_code=409, detail="Group already exists")
    res = service.update_group(group_id, GroupBase(name=req.name, description=req.description))
    if not res:
        raise HTTPException(status_code=404, detail="Group not found")
    return res


@router.delete("/group/{group_id}", response_model=DeleteGroupResponse)
@protected
def delete_group(group_id: int, service: GroupServiceDep) -> DeleteGroupResponse:
    if not service.get_group_by_id(group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    service.delete_group(group_id)
    return DeleteGroupResponse(msg="Grupo borrado con éxito")


@router.post("/group/{group_id}/user/{user_id}", response_model=Sequence[MemberResponse], status_code=201)
@protected
def add_member(
    group_id: int, user_id: int, service: GroupServiceDep, user_service: UserServiceDep
) -> list[MemberResponse]:
    group = service.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not user_service.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if service.get_membership(group_id, user_id):
        raise HTTPException(status_code=409, detail="User already in group")
    service.add_member(group_id, user_id)
    return _members(group)


@router.delete("/group/{group_id}/user/{user_id}", response_model=Sequence[MemberResponse])
@protected
def remove_member(group_id: int, user_id: int, service: GroupServiceDep) -> list[MemberResponse]:
    group = service.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    membership = service.get_membership(group_id, user_id)
    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of the group")
    service.remove_member(membership)
    return _members(group)


@router.put("/group/{group_id}/leader/{user_id}", response_model=Sequence[MemberResponse])
@protected
def set_leader(group_id: int, user_id: int, service: GroupServiceDep) -> list[MemberResponse]:
    group = service.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not service.get_membership(group_id, user_id):
        raise HTTPException(status_code=409, detail="Only a member can be leader")
    return _members(service.set_leader(group, user_id))


@router.get("/group/{group_id}/user", response_model=Sequence[MemberResponse])
@protected
def get_members(group_id: int, service: GroupServiceDep) -> list[MemberResponse]:
    group = service.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return _members(group)
```

Detalles para marcar:
- Los códigos HTTP salen de las reglas: **404** si algo no existe, **409** si la operación choca con el estado actual (ya es miembro / no es miembro para ser líder).
- La validación vive en el router (como en `api/roles.py`); el repositorio solo persiste.
- `group.memberships` se refresca con `session.refresh` dentro del repositorio; por eso `add_member` y `remove_member` devuelven la lista leída de `group` después de commitear. Si algún alumno ve la lista desactualizada, el remedio es `session.refresh(group)` en el repositorio.

## Paso 8 — Registrar el router: `main.py`

```python
from api import groups, login, permissions, roles, users   # agregar groups

app.include_router(groups.router)                           # agregar
```

Este import es el que registra `Group` y `Membership` en el metadata antes de `create_db_and_tables()`.

**Prueba manual:** `.venv/bin/uvicorn main:app --reload`, abrir `/docs`, hacer login (`mgomez@email.com` / `123`), "Authorize", y probar: crear grupo → unir usuarios 1 y 2 → asignar líder → listar miembros.

---

## Paso 9 — Tests: `tests/api/test_groups.py` (nuevo)

Usa las fixtures de `tests/conftest.py` (`client`, `auth_headers`; el seed crea 3 usuarios con ids 1, 2 y 3).

```python
import pytest


@pytest.fixture(name="group_id")
def group_id_fixture(client, auth_headers) -> int:
    res = client.post("/group", json={"name": "Backend", "description": "Grupo de estudio"}, headers=auth_headers)
    return res.json()["id"]


# --- CRUD ---
def test_create_group_ok(client, auth_headers):
    res = client.post("/group", json={"name": "Backend"}, headers=auth_headers)
    assert res.status_code == 201
    assert client.get(f"/group/{res.json()['id']}", headers=auth_headers).json()["name"] == "Backend"


def test_create_group_duplicate(client, auth_headers, group_id):
    res = client.post("/group", json={"name": "Backend"}, headers=auth_headers)
    assert res.status_code == 409


def test_get_group_fail(client, auth_headers):
    assert client.get("/group/120", headers=auth_headers).status_code == 404


def test_update_group_ok(client, auth_headers, group_id):
    res = client.patch(f"/group/{group_id}", json={"name": "Frontend"}, headers=auth_headers)
    assert res.status_code == 200
    assert client.get(f"/group/{group_id}", headers=auth_headers).json()["name"] == "Frontend"


def test_delete_group_fail(client, auth_headers):
    assert client.delete("/group/120", headers=auth_headers).status_code == 404


# --- Membresías ---
def test_add_member_ok(client, auth_headers, group_id):
    res = client.post(f"/group/{group_id}/user/1", headers=auth_headers)
    assert res.status_code == 201
    members = client.get(f"/group/{group_id}/user", headers=auth_headers).json()
    assert [m["id"] for m in members] == [1]
    assert members[0]["is_leader"] is False
    assert members[0]["joined_at"]                      # dato propio de la relación


def test_add_member_twice_conflict(client, auth_headers, group_id):
    client.post(f"/group/{group_id}/user/1", headers=auth_headers)
    res = client.post(f"/group/{group_id}/user/1", headers=auth_headers)
    assert res.status_code == 409


def test_add_member_not_found(client, auth_headers, group_id):
    assert client.post("/group/120/user/1", headers=auth_headers).status_code == 404
    assert client.post(f"/group/{group_id}/user/120", headers=auth_headers).status_code == 404


def test_remove_member_ok(client, auth_headers, group_id):
    client.post(f"/group/{group_id}/user/1", headers=auth_headers)
    res = client.delete(f"/group/{group_id}/user/1", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_remove_member_not_member(client, auth_headers, group_id):
    assert client.delete(f"/group/{group_id}/user/1", headers=auth_headers).status_code == 404


# --- Líder ---
def test_set_leader_ok(client, auth_headers, group_id):
    client.post(f"/group/{group_id}/user/1", headers=auth_headers)
    res = client.put(f"/group/{group_id}/leader/1", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()[0]["is_leader"] is True


def test_set_leader_is_unique(client, auth_headers, group_id):
    client.post(f"/group/{group_id}/user/1", headers=auth_headers)
    client.post(f"/group/{group_id}/user/2", headers=auth_headers)
    client.put(f"/group/{group_id}/leader/1", headers=auth_headers)
    res = client.put(f"/group/{group_id}/leader/2", headers=auth_headers)
    leaders = [m["id"] for m in res.json() if m["is_leader"]]
    assert leaders == [2]


def test_set_leader_requires_membership(client, auth_headers, group_id):
    res = client.put(f"/group/{group_id}/leader/1", headers=auth_headers)
    assert res.status_code == 409


# --- Cascada ---
def test_delete_group_keeps_users(client, auth_headers, group_id):
    client.post(f"/group/{group_id}/user/1", headers=auth_headers)
    assert client.delete(f"/group/{group_id}", headers=auth_headers).status_code == 200
    assert client.get(f"/group/{group_id}", headers=auth_headers).status_code == 404
    assert client.get("/user/1", headers=auth_headers).status_code == 200


# --- Sin token ---
@pytest.mark.parametrize("method, path", [("get", "/group"), ("post", "/group"), ("get", "/group/1/user")])
def test_group_endpoints_require_auth(client, method, path):
    assert getattr(client, method)(path).status_code in (401, 403)
```

Ejecutar desde `clase-1-sqlmodel`:
```bash
.venv/bin/pytest tests/api/test_groups.py -v
.venv/bin/pytest --cov          # suite completa; el coverage no debe bajar
.venv/bin/ruff check .
```

> `tests/api/test_auth.py` usa el `database.db` real (no la base en memoria), que se crea al levantar la app una vez. Si clonás el proyecto desde cero y esos tests fallan con `OperationalError`, corré `uvicorn main:app` una vez y volvé a probar.

---

## Checklist de la clase
- [ ] `model/groups.py`: `Membership` con PK compuesta y atributos extra
- [ ] `UserDB.memberships` con `cascade_delete`
- [ ] Repositorio → servicio → dependencias → modelos de API → router → `main.py`
- [ ] Tests: CRUD, 404/409, un solo líder, cascada
- [ ] Probado a mano en `/docs`

## Preguntas para discutir
1. ¿Por qué `UserRole` es un `link_model` y `Membership` no? ¿Qué pasaría si quisiéramos `joined_at` en `UserRole`?
2. ¿Qué dos relaciones 1-N forman un N-N con atributos?
3. ¿Dónde pondrías la regla "máximo 5 miembros por grupo"? ¿Qué código HTTP devolverías?
4. Extensión: `GET /user/{id}/group` (grupos de un usuario) y seed de grupos en `repositories/seed.py`.

---
*Código verificado: aplicado sobre una copia de `clase-1-sqlmodel`, la suite completa pasa (84 tests, 17 nuevos) y `ruff check` no reporta errores.*
