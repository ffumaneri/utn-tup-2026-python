from sqlmodel import select

from model.roles import Permission, Role
from model.users import UserDB
from repositories.seed import seed_roles_and_permissions, seed_user_roles


def test_seed_roles_and_permissions(session):
    seed_roles_and_permissions(session)

    perms = {p.name for p in session.exec(select(Permission)).all()}
    assert perms == {"write_users", "read_users", "delete_users", "update_users"}

    roles = {r.name: {p.name for p in r.permissions} for r in session.exec(select(Role)).all()}
    assert roles == {"ADMIN": perms, "REGULAR": {"read_users"}}


def test_seed_is_idempotent(session):
    seed_roles_and_permissions(session)
    seed_roles_and_permissions(session)
    assert len(session.exec(select(Role)).all()) == 2
    assert len(session.exec(select(Permission)).all()) == 4


def test_seed_user_roles_one_admin_rest_regular(session, seed):
    seed_user_roles(session)  # idempotente: seed ya lo ejecutó una vez
    roles = {u.email: [r.name for r in u.roles] for u in session.exec(select(UserDB)).all()}
    assert roles == {
        "mgomez@email.com": ["ADMIN"],
        "sfer@email.com": ["REGULAR"],
        "cma@email.com": ["REGULAR"],
    }
