from sqlmodel import Session, select

from model.roles import ADMIN_ROLE, REGULAR_ROLE, Permission, Role
from model.users import UserDB

ADMIN_EMAIL = "mgomez@email.com"

PERMISSION_NAMES = ["write_users", "read_users", "delete_users", "update_users"]
ROLE_PERMISSIONS = {
    ADMIN_ROLE: PERMISSION_NAMES,
    REGULAR_ROLE: ["read_users"],
}


def seed_roles_and_permissions(session: Session) -> None:
    if session.exec(select(Role)).first():
        return
    permissions = {name: Permission(name=name) for name in PERMISSION_NAMES}
    session.add_all(permissions.values())
    session.add_all(
        Role(name=role, permissions=[permissions[p] for p in names]) for role, names in ROLE_PERMISSIONS.items()
    )
    session.commit()


def seed_user_roles(session: Session) -> None:
    # Un usuario admin y el resto REGULAR; solo toca usuarios que todavía no tienen rol.
    roles = {r.name: r for r in session.exec(select(Role)).all()}
    if ADMIN_ROLE not in roles or REGULAR_ROLE not in roles:
        return
    for user in session.exec(select(UserDB)).all():
        if not user.roles:
            user.roles = [roles[ADMIN_ROLE if user.email == ADMIN_EMAIL else REGULAR_ROLE]]
            session.add(user)
    session.commit()
