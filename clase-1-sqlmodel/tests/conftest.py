import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from model.users import Country, UserDB
from repositories.database import get_session
from repositories.seed import seed_roles_and_permissions, seed_user_roles
from utils.hash import hash_password


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",                               # en memoria
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,                      # ver nota abajo
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(name="seed")
def seed_fixture(session: Session):
    session.add_all([Country(id=1, name="Argentina"), Country(id=2, name="Brasil")])
    session.commit()

    pwd = hash_password("123")      # las contraseñas se guardan hasheadas
    session.add_all([
        UserDB(name="Martina Gómez", email="mgomez@email.com", age=28, country_id=1, password=pwd),
        UserDB(name="Santiago Fernández", email="sfer@email.com", age=34, country_id=1, password=pwd),
        UserDB(name="Camila Martínez", email="cma@email.com", age=15, country_id=2, password=pwd),
    ])
    session.commit()

    seed_roles_and_permissions(session)
    seed_user_roles(session)

@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient, seed):
    res = client.post("/login", json={"email": "mgomez@email.com","password": "123"})
    return {"Authorization": f"Bearer {res.json()["token"]}"}