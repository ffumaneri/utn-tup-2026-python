# Connecting to PostgreSQL

The app supports **SQLite** (default) and **PostgreSQL**. The backend is chosen at startup with environment variables; no code changes are needed to switch.

| Variable       | Values                      | Default       | Description                                           |
|----------------|-----------------------------|---------------|-------------------------------------------------------|
| `DB_ENGINE`    | `sqlite` \| `postgresql`    | `sqlite`      | Selects the backend.                                  |
| `SQLITE_FILE`  | file path                   | `database.db` | SQLite file (only when `DB_ENGINE=sqlite`).           |
| `DATABASE_URL` | SQLAlchemy URL              | —             | **Required** when `DB_ENGINE=postgresql`.             |

The logic lives in `repositories/database.py` (see [Code change](#code-change) below). If `DB_ENGINE` has an unknown value, or `DATABASE_URL` is missing for PostgreSQL, the app fails fast at startup.

## Code change

Replace the contents of `repositories/database.py` with:

```python
import os

from sqlmodel import Session, SQLModel, create_engine

# DB_ENGINE selects the backend at startup: "sqlite" (default) or "postgresql".
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()

if DB_ENGINE == "sqlite":
    sqlite_file_name = os.getenv("SQLITE_FILE", "database.db")
    database_url = f"sqlite:///{sqlite_file_name}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
elif DB_ENGINE in ("postgresql", "postgres"):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DB_ENGINE=postgresql requires DATABASE_URL to be set")
    engine = create_engine(database_url, pool_pre_ping=True)
else:
    raise RuntimeError(f"Unsupported DB_ENGINE: {DB_ENGINE!r} (use 'sqlite' or 'postgresql')")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
```

No other file needs to change: `main.py` and the repositories keep using `database.engine` and `get_session`.

## 1. Install the driver

```bash
pip install "psycopg[binary]"
```

Add `psycopg[binary]` to `requirements.txt` as well. (The `psycopg2-binary` driver also works; use the `postgresql+psycopg2://` scheme in that case.)

## 2. Start PostgreSQL

Quickest option with Docker:

```bash
docker run --name app-postgres -d \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=appdb \
  -p 5432:5432 postgres:16
```

## 3. Run the app

**SQLite (default):**

```bash
uvicorn main:app --reload
```

**PostgreSQL:**

```bash
export DB_ENGINE=postgresql
export DATABASE_URL="postgresql+psycopg://app:secret@localhost:5432/appdb"
uvicorn main:app --reload
```

URL format: `postgresql+psycopg://<user>:<password>@<host>:<port>/<database>`. Special characters in the password must be URL-encoded (e.g. `@` → `%40`).

Tables are created automatically on startup by `create_db_and_tables()` (`SQLModel.metadata.create_all`), and the seed runs as with SQLite.

## 4. Verify

```bash
docker exec -it app-postgres psql -U app -d appdb -c '\dt'
```

You should see the app's tables (users, roles, permissions, ...).

## Notes

- **Tests** use their own in-memory SQLite engine (`tests/conftest.py`), so they are unaffected by these variables.
- **Migrations:** `create_all` only creates missing tables; it does not alter existing ones. For schema changes on PostgreSQL, use Alembic.
- **Existing data:** switching backends does not copy data. `database.db` stays untouched when running against PostgreSQL.
- **Secrets:** never commit `DATABASE_URL` with real credentials; keep it in your shell, a `.env` file ignored by git, or your deploy platform's secrets.
