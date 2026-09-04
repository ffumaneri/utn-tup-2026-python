
from typing import Annotated, Sequence

from fastapi import Depends, FastAPI, Query
from sqlmodel import Field, SQLModel, Session, create_engine, select

# Se define el modelo


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)


# Code above omitted 👆

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_dummy_users():
    with Session(engine) as session:
        if session.exec(select(User)).first():
            return
        names = [
            "Martina Gómez",
            "Santiago Fernández",
            "Valentina López",
            "Mateo Rodríguez",
            "Camila Martínez",
            "Lucas Pérez",
            "Sofía García",
            "Nicolás Sánchez",
            "Julieta Díaz",
            "Tomás Romero",
        ]
        users = [User(name=name) for name in names]
        session.add_all(users)
        session.commit()


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_dummy_users()


@app.post("/user")
def create_user(user: User, session: SessionDep) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/user")
def get_user(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> Sequence[User]:
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users
