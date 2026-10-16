# Guía paso a paso: tests de la API con pytest y HTTPX

> Esta guía es material de estudio. El código que aparece acá es **ilustrativo**:
> ningún archivo del proyecto fue modificado para escribirla. La idea es que
> lo escriban ustedes mismos, paso a paso, siguiendo esta guía.
> (Todos los ejemplos fueron ejecutados contra este proyecto y pasan: 21 tests en verde.)

## 0. Por qué testear

Hasta ahora probamos la API a mano desde Swagger: hacemos login, copiamos el
token, lo pegamos en **Authorize** y vamos probando endpoint por endpoint.
Eso sirve para explorar, pero:

- Es lento y hay que repetirlo cada vez que cambiamos algo.
- Es fácil olvidarse de probar algún caso (¿qué pasa sin token? ¿y con un id que no existe?).
- Si rompemos algo que andaba, nos enteramos tarde.

Un **test automático** es código que hace esas mismas requests por nosotros y
verifica el resultado. Lo corremos con un solo comando.

Herramientas que vamos a usar:

| Herramienta | Para qué sirve |
|---|---|
| **pytest** | Encuentra y ejecuta los tests, y muestra qué falló. Aporta *fixtures* (preparación reutilizable). |
| **HTTPX** | Cliente HTTP de Python. Es la base de `TestClient` de FastAPI. |
| **`TestClient`** (`fastapi.testclient`) | Llama a nuestra app **sin levantar un servidor**: le pasa las requests directo a la aplicación. |

Los tests que vamos a escribir son de **integración**: pasan por middleware,
router, servicio, repositorio y base de datos (una de prueba, en memoria).

## 1. Instalación y estructura

`httpx` ya está instalado (lo necesita `TestClient`). Falta `pytest`:

```bash
pip install pytest
# o, si usan uv:  uv add --dev pytest
```

Creamos una carpeta `tests/` en la raíz del proyecto (al lado de `main.py`):

```
clase-1-sqlmodel/
├── main.py
├── dependencies.py
├── pyproject.toml
└── tests/
    ├── conftest.py       # fixtures compartidas
    ├── test_login.py
    └── test_users.py
```

Nuestros imports son "planos" (`from main import app`, `from model.users import ...`),
así que pytest tiene que saber que la raíz del proyecto está en el path. Agregamos
esto al final de `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

Reglas de pytest para que encuentre las cosas:

- Los archivos se llaman `test_*.py`.
- Las funciones se llaman `test_*`.
- `conftest.py` se carga automáticamente; lo que definimos ahí está disponible en todos los tests sin importarlo.

## 2. Nuestro primer test

Antes de preocuparnos por la base de datos, probemos algo que no la necesita.
Creamos `tests/test_primero.py`:

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_docs_es_publico():
    res = client.get("/docs")
    assert res.status_code == 200


def test_users_sin_token_devuelve_401():
    res = client.get("/user")
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing or invalid Authorization header"
```

Lo corremos:

```bash
pytest -v
```

Cada `assert` es una verificación: si es falso, el test falla y pytest nos
muestra los valores que comparó. El segundo test pasa porque el middleware
`JWTAuthMW` corta la request **antes** de llegar a la base de datos.

> **Ojo:** `TestClient(app)` sin `with` **no** ejecuta los eventos de `startup`
> de `main.py`. Es lo que queremos: así no se crea ni se llena `database.db`.
> Si lo usaran como `with TestClient(app) as client:` sí correría `on_startup`
> y se tocaría la base real.

El segundo test funcionó sin base de datos, pero cuando pidamos usuarios
vamos a necesitarla. Ahí viene el problema.

## 3. Aislar la base de datos

`repositories/database.py` crea un `engine` apuntando a `database.db` y la
dependencia `get_session` entrega sesiones de ese engine. Si los tests usan
eso, **escriben en la base real** (borran usuarios, crean otros...). Inaceptable.

La solución: FastAPI permite **reemplazar una dependencia** con
`app.dependency_overrides`. Reemplazamos `get_session` por una que use una base
SQLite **en memoria**, nueva para cada test.

Creamos `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from repositories.database import get_session


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
```

Cosas para entender:

- **Fixture**: función marcada con `@pytest.fixture` que prepara algo para un test.
  Si un test tiene un parámetro con el mismo nombre que una fixture, pytest la
  ejecuta y se la pasa. Por ejemplo `def test_algo(client):` recibe el `TestClient` ya configurado.
- **`yield`**: lo que está antes se ejecuta antes del test (preparación); lo que está
  después, al terminar (limpieza). Acá, `dependency_overrides.clear()` deja la
  app como estaba para que un test no afecte a otro.
- **`StaticPool`**: una base SQLite en memoria vive solo dentro de *una* conexión.
  Sin `StaticPool`, cada conexión vería una base vacía distinta y obtendrían errores
  tipo `no such table: userdb`. Con `StaticPool` todas comparten la misma.
- Las fixtures son por **función** (valor por defecto): cada test arranca con
  una base nueva y vacía. Los tests no se afectan entre sí.

## 4. Datos de prueba

Con la base vacía no hay nada para listar ni un usuario con el cual loguearse.
Agregamos a `conftest.py` una fixture que carga datos (parecida a
`create_dummy_data` de `main.py`, pero más chica y controlada):

```python
from model.users import Country, UserDB
from utils.hash import hash_password


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
```

> **Importante:** hay que usar `hash_password`. El login compara con
> `verify_password`, que espera un hash; si guardáramos `"123"` en texto plano
> el login siempre fallaría.

Como sabemos exactamente qué datos hay (3 usuarios, ids 1, 2 y 3; dos mayores
de edad), podemos escribir asserts precisos.

## 5. Tests de login

`tests/test_login.py`:

```python
def test_login_ok(client, seed):
    res = client.post("/login", json={"email": "mgomez@email.com", "password": "123"})
    assert res.status_code == 200
    assert res.json()["msg"] == "ok"
    assert res.json()["token"]


def test_login_password_incorrecta(client, seed):
    res = client.post("/login", json={"email": "mgomez@email.com", "password": "mal"})
    assert res.status_code == 401


def test_login_usuario_inexistente(client, seed):
    res = client.post("/login", json={"email": "nadie@email.com", "password": "123"})
    assert res.status_code == 401
```

Fijense que `seed` aparece como parámetro aunque no lo usemos dentro del test:
alcanza con pedirla para que pytest la ejecute antes.

## 6. Autenticación en los tests

Todas las rutas `/user*` exigen `Authorization: Bearer <token>`. En vez de
repetir el login en cada test, hacemos una fixture que lo hace una vez y
devuelve los headers listos. Agregar a `conftest.py`:

```python
@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient, seed):
    res = client.post("/login", json={"email": "mgomez@email.com", "password": "123"})
    return {"Authorization": f"Bearer {res.json()['token']}"}
```

Uso: `client.get("/user", headers=auth_headers)`.

**Alternativa:** generar el token directamente con el servicio JWT, sin pasar por `/login`:

```python
from dependencies import get_jwt_service

token = get_jwt_service().create_access_token({"sub": "sfer@email.com"})
headers = {"Authorization": f"Bearer {token}"}
```

(El `sub` tiene que ser el email de un usuario que exista en la base de prueba.)

## 7. Tests de la API de usuarios

`tests/test_users.py`:

```python
def test_sin_token_devuelve_401(client):
    assert client.get("/user").status_code == 401


def test_token_invalido_devuelve_401(client):
    res = client.get("/user", headers={"Authorization": "Bearer basura"})
    assert res.status_code == 401


def test_get_users(client, auth_headers):
    res = client.get("/user", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 3


def test_get_user_by_id(client, auth_headers):
    res = client.get("/user/1", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Martina Gómez"
    assert res.json()["country"]["name"] == "Argentina"


def test_get_user_inexistente(client, auth_headers):
    assert client.get("/user/999", headers=auth_headers).status_code == 404


def test_search_user(client, auth_headers):
    res = client.get("/user/search/Mart", headers=auth_headers)
    assert {u["name"] for u in res.json()} == {"Martina Gómez", "Camila Martínez"}


def test_mayores(client, auth_headers):
    res = client.get("/user_mayores", headers=auth_headers)
    assert len(res.json()) == 2


def test_create_user(client, auth_headers):
    body = {"name": "Nuevo", "age": 20, "country_id": 1,
            "email": "nuevo@email.com", "password": "abcd1234"}
    res = client.post("/user", json=body, headers=auth_headers)
    assert res.status_code == 200
    new_id = res.json()["id"]
    # verificamos que realmente quedó guardado
    assert client.get(f"/user/{new_id}", headers=auth_headers).json()["name"] == "Nuevo"


def test_update_user(client, auth_headers):
    body = {"name": "Martina Editada", "age": 29, "country_id": 2,
            "email": "mgomez@email.com", "password": "abcd1234"}
    res = client.patch("/user/1", json=body, headers=auth_headers)
    assert res.status_code == 200
    assert client.get("/user/1", headers=auth_headers).json()["name"] == "Martina Editada"


def test_delete_user(client, auth_headers):
    assert client.delete("/user/2", headers=auth_headers).status_code == 200
    assert client.get("/user/2", headers=auth_headers).status_code == 404
```

Patrón que se repite en los tests de escritura: **actuar** (POST/PATCH/DELETE)
y después **verificar con otra request** que el cambio quedó hecho. No alcanza
con mirar el código de respuesta.

## 8. `parametrize`: un test, muchos casos

Queremos comprobar que **todos** los endpoints protegidos devuelven 401 sin
token. Escribir un test por endpoint es repetitivo; `pytest.mark.parametrize`
corre el mismo test con distintos datos:

```python
import pytest


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/user"),
        ("get", "/user/1"),
        ("get", "/user/search/ma"),
        ("get", "/user_mayores"),
        ("delete", "/user/1"),
    ],
)
def test_endpoints_protegidos(client, method, path):
    res = getattr(client, method)(path)
    assert res.status_code == 401
```

pytest lo muestra como 5 tests separados, y si uno falla dice cuál.
Si mañana agregamos un endpoint, sumamos una línea a la lista.

## 9. Usar HTTPX directamente (async)

`TestClient` es **síncrono**: por dentro usa HTTPX pero esconde la parte `async`.
Para el curso alcanza y sobra. Pero también se puede usar HTTPX "a mano" con
`AsyncClient`, que es lo que se usa cuando los tests mismos son `async`
(por ejemplo si la app usara bases de datos asíncronas).

```python
import httpx
import pytest

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_login_async(client, seed):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/login", json={"email": "mgomez@email.com", "password": "123"})
    assert res.status_code == 200
```

- `ASGITransport(app=app)` le dice a HTTPX que, en vez de salir por la red,
  le hable directo a la app.
- `@pytest.mark.anyio` viene con el paquete `anyio`, que ya está instalado
  porque FastAPI lo usa. (La alternativa popular es `pytest-asyncio`.)
- Acá pedimos las fixtures `client` y `seed` solo por su efecto: dejan
  la base en memoria configurada con datos.

## 10. Errores comunes

| Síntoma | Causa |
|---|---|
| `ModuleNotFoundError: No module named 'main'` | Falta `pythonpath = ["."]` en `pyproject.toml` (sección 1). |
| `no such table: userdb` | Falta `poolclass=StaticPool` o `SQLModel.metadata.create_all(engine)` (sección 3). |
| El login siempre da 401 en los tests | Guardaron la contraseña sin `hash_password` en el `seed`. |
| Todo da 401 aunque mandás token | El header debe ser exactamente `Authorization: Bearer <token>`. |
| Un test pasa solo pero falla junto con otros | Estado compartido: no limpiaron `dependency_overrides` o usaron la base real. |
| Aparece/cambia `database.db` después de correr tests | Usaron `with TestClient(app)` o no sobrescribieron `get_session`. |
| Warnings de `httpx`/`on_event`/`crypt` | Son avisos de deprecación de las librerías, no de tu código. Los tests igual funcionan. |

Buenas prácticas:

- Un test verifica **una cosa** y tiene un nombre que dice cuál (`test_get_user_inexistente`).
- Los tests no dependen del orden ni de lo que hizo otro test.
- Probar también los casos de error (401, 404, 422), no solo el "camino feliz".
- Nunca apuntar los tests a la base real.

## 11. Ejercicios

1. Escribí un test para `GET /user/me/id` que verifique que devuelve el id del usuario logueado (`{"id": 1}` para `mgomez@email.com`).
2. Verificá que `POST /user` con un body incompleto (sin `email`) devuelve **422**.
3. Verificá que un token **vencido** devuelve 401. Pista: `JWTService("my-secret-key", expire_minutes=-1).create_access_token(...)`.
4. Verificá que `GET /user?limit=2` devuelve solo 2 usuarios y que `limit=101` devuelve 422.
5. Agregá `PATCH /user/999` y comprobá que devuelve 404.
6. Instalá `pytest-cov` (`pip install pytest-cov`) y corré `pytest --cov=. --cov-report=term-missing`. ¿Qué líneas no están cubiertas?
7. Elegí un test de la guía, rompé a propósito el código de la API (por ejemplo cambiá un status code) y comprobá que el test lo detecta.

## 12. Cómo correr todo

```bash
pytest -v                      # todos, con detalle
pytest tests/test_users.py     # un archivo
pytest -k "delete"             # solo los tests cuyo nombre contenga "delete"
pytest -x                      # frena en el primer fallo
```
