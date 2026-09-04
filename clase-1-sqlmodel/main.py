
from typing import Annotated, Sequence

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, SQLModel, Session, create_engine, select

# Se define el modelo


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int


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
        names_and_ages = [
            ("Martina Gómez", 28),
            ("Santiago Fernández", 34),
            ("Valentina López", 22),
            ("Mateo Rodríguez", 45),
            ("Camila Martínez", 19),
            ("Lucas Pérez", 31),
            ("Sofía García", 27),
            ("Nicolás Sánchez", 40),
            ("Julieta Díaz", 24),
            ("Tomás Romero", 37),
        ]
        users = [
            User(name=name, age=age) for name, age in names_and_ages
        ]
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


@app.get("/user/{user_id}")
def get_user_by_id(user_id: int, session: SessionDep) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
