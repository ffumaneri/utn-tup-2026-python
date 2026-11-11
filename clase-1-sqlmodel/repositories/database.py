from sqlmodel import Session, SQLModel, create_engine

DB_ENGINE = "postgres"

if DB_ENGINE == "sqlite":
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)
elif DB_ENGINE == "postgres":
    database_url = "postgresql+psycopg://postgres:admin@localhost:5433/utn"
    engine = create_engine(database_url, pool_pre_ping=True)
else:
    raise RuntimeError(f"database engine not supported {DB_ENGINE} use 'sqlite' or 'postgres'")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



def get_session():
    with Session(engine) as session:
        yield session