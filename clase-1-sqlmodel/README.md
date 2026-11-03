# clase-1-sqlmodel

REST API built with FastAPI and SQLModel (SQLite). It has JWT authentication and role-based permissions (users, roles, permissions).

## Requirements

- Python 3.12 or newer
- pip

## Installation

```bash
# 1. create a virtual environment
python3 -m venv .venv

# 2. activate it
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. install the dependencies
pip install -r requirements.txt
```

Always activate `.venv` before running the app or the tests. If you use your global Python you will get errors such as `ModuleNotFoundError: No module named 'jwt'`.

## Run the app

```bash
uvicorn main:app --reload
```

- API docs (Swagger): http://127.0.0.1:8000/docs
- On startup the app creates `database.db` (SQLite) and seeds countries, users, roles and permissions.
- Log in with `POST /login` using `mgomez@email.com` / `123` (ADMIN role). Other seeded users also use the password `123`.
- Click **Authorize** in Swagger and paste the returned token to call protected endpoints.

## Run the tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=api --cov=services --cov=repositories --cov-report=term-missing
```

Tests use an in-memory SQLite database, so they do not touch `database.db`.

## Troubleshooting

- `ModuleNotFoundError: No module named 'jwt'`: the virtual environment is not active, or the package is missing. Run `source .venv/bin/activate` and `pip install -r requirements.txt`. The package is `PyJWT`, not `jwt`.
- `pytest: error: unrecognized arguments: --cov`: `pytest-cov` is not installed in the active environment. Reinstall the requirements.

## Project structure

```
main.py            FastAPI app, middlewares and startup seed
api/               routers (users, login, roles, permissions) and middlewares
services/          business logic (users, login, JWT)
repositories/      database engine, data access and seed data
model/             SQLModel tables and schemas
utils/             helpers (password hashing)
tests/             pytest tests
docs/              guides (JWT, testing, group membership)
```
