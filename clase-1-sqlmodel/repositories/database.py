import os

from sqlmodel import Session, SQLModel, create_engine

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()

if DB_ENGINE == "sqlite":
    print("conectado a sqllite")
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)
elif DB_ENGINE == "postgres":
    print("conectado a postgres")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("postgres url has not been set up")
    engine = create_engine(database_url, pool_pre_ping=True)
else:
    raise RuntimeError(f"database engine not supported {DB_ENGINE} use 'sqlite' or 'postgres'")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



def get_session():
    with Session(engine) as session:
        yield session