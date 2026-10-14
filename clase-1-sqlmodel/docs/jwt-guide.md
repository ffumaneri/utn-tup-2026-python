# Guía paso a paso: autenticación con JWT

> Esta guía es material de estudio. El código que aparece acá es **ilustrativo**:
> ningún archivo del proyecto fue modificado para escribirla. La idea es que
> lo escriban ustedes mismos, paso a paso, siguiendo esta guía.

## 0. Por qué JWT

Hoy el proyecto tiene dos mecanismos de "seguridad" que no hablan entre sí:

1. `POST /login` (`api/login.py` → `services/login.py`) compara la contraseña
   en texto plano y, si coincide, devuelve un token **hardcodeado**:

   ```python
   # services/login.py (hoy)
   class LoginService():
       def __init__(self, repo: UserRepositoryDep):
           self.repo = repo
       def login(self, email: str, pwd: str) -> bool:
           user = self.repo.get_by_email(email)
           if not user:
               return False
           return user.password == pwd
   ```

   ```python
   # api/login.py (hoy)
   @router.post("/login", response_model=LoginResponse)
   def login(req: Login, service: LoginServiceDep) -> LoginResponse:
       valid = service.login(req.email, req.password)
       if not valid:
           raise HTTPException(status_code=401, detail="User/password incorrect")
       return LoginResponse(msg="ok", token="121456")
   ```

   Ese `"121456"` es siempre el mismo string. No identifica a nadie, no
   expira, y nada lo verifica después.

2. `api/middlewares/check_apikey.py` (`CheckApikeyMW`) exige en **todas**
   las rutas (salvo `/docs`, `/openapi.json` y `/login`) un header
   `x-api-key: 123`. Es una clave única, compartida por todos: sabe que
   *alguien con la clave* está llamando, pero no sabe **quién**.

Un **JWT** (JSON Web Token) resuelve ambos problemas. Es un token firmado
que el servidor genera en el login, y que contiene datos del usuario (por
ejemplo su email) y una fecha de expiración. El flujo completo es:

```
1. Cliente → POST /login (email, password)
2. Servidor verifica la contraseña, firma un JWT con datos del user
3. Servidor → responde { "token": "<jwt>" }
4. Cliente guarda el token y lo manda en cada request:
   Authorization: Bearer <jwt>
5. Servidor, en cada request, decodifica y valida el token,
   y sabe exactamente qué usuario está llamando
```

Un JWT tiene tres partes separadas por puntos: `header.payload.signature`.
El `payload` es el dato (por ejemplo `{"sub": "user@mail.com", "exp": ...}`),
y la `signature` es una firma criptográfica hecha con una clave secreta que
solo el servidor conoce — por eso nadie puede fabricar o alterar un token
válido sin conocer esa clave.

Instalamos las dos librerías que vamos a usar:

```bash
pip install pyjwt "passlib[bcrypt]"
```

(El proyecto ya tiene `pydantic-settings` instalado, que es una buena forma
de leer la clave secreta desde una variable de entorno en vez de
hardcodearla — lo mencionamos en el paso 2.)

---

## Paso 1 — Hashear las contraseñas

Antes de tocar el login, hay un problema previo: en `model/users.py` el
campo `password` se guarda **tal cual lo mandó el usuario**:

```python
# model/users.py (hoy)
class User(SQLModel):
    name: str = Field(index=True)
    age: int
    country_id: int | None = Field(default=None, foreign_key="country.id")
    password: str = Field(max_length=10, min_length=4)
    email: EmailStr = Field(unique=True, index=True)
```

Y `services/login.py` compara la contraseña recibida con `==` contra ese
valor guardado en texto plano. Si alguien accede a la base de datos, tiene
todas las contraseñas de todos los usuarios. Emitir un JWT sobre esta base
sería resolver un problema y dejar el más grave sin tocar.

La regla es: **nunca guardamos ni comparamos contraseñas en texto plano**.
Guardamos un *hash* (una transformación de un solo sentido) y comparamos
hashes.

```python
# ejemplo: un helper de hashing
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

- `hash_password` se usa al **crear** un usuario (en `UserRepository.create_user`,
  antes de guardar, en vez de guardar `userBase.password` tal cual).
- `verify_password` se usa al **loguear**, comparando la contraseña que
  llega en el request contra el hash guardado — nunca comparando strings
  directamente.

Con esto resuelto, el `login` de hoy:

```python
return user.password == pwd  # mal: compara texto plano
```

pasaría a ser:

```python
return verify_password(pwd, user.password)  # bien: compara contra el hash
```

---

## Paso 2 — La clase `JWTService`

Este es el corazón de la guía: una clase que sabe **crear** y **decodificar**
tokens. Siguiendo el mismo patrón que ya usa el proyecto para sus clases de
servicio (`LoginService`, `UserService` en `services/`), la ubicaríamos en
un nuevo archivo `services/jwt_service.py`:

```python
# services/jwt_service.py
import jwt
from datetime import datetime, timedelta, timezone


class JWTService:
    def __init__(self, secret_key: str, algorithm: str = "HS256", expire_minutes: int = 30):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        to_encode["exp"] = expire
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

Explicación método por método:

- **`__init__`**: recibe la clave secreta (`secret_key`), el algoritmo de
  firma (`HS256` es el más común para este caso) y cuántos minutos dura un
  token antes de expirar. La `secret_key` **nunca** va hardcodeada en el
  código ni commiteada al repo — se lee de una variable de entorno. Como el
  proyecto ya usa `pydantic-settings`, una forma prolija sería definir una
  clase `Settings(BaseSettings)` con un campo `jwt_secret_key: str` que lo
  lea de `.env`, e inyectar `JWTService` con ese valor.

- **`create_access_token`**: recibe un diccionario con los datos que
  queremos guardar en el token (el *payload*) — típicamente
  `{"sub": user.email}` (`sub` = *subject*, la convención estándar de JWT
  para "a quién pertenece este token"). **Nunca** ponemos la contraseña ni
  datos sensibles acá, porque el payload de un JWT no está encriptado, solo
  firmado — cualquiera puede leerlo (probá pegar un JWT en jwt.io), lo único
  que no puede es *alterarlo* sin invalidar la firma. Le agrega el campo
  `exp` (expiration) con la fecha/hora en que deja de ser válido, y lo firma
  con `jwt.encode`.

- **`decode_token`**: hace lo inverso — verifica la firma y la expiración.
  Si el token fue alterado o la firma no coincide, `jwt.decode` lanza
  `InvalidTokenError`; si ya expiró, lanza `ExpiredSignatureError`. En
  ambos casos devolvemos `None` para que quien llama decida qué hacer (en
  nuestro caso, devolver un 401).

---

## Paso 3 — Emitir el token en `/login`

Con `JWTService` y el hashing del paso 1, `services/login.py` pasaría de
devolver un `bool` a devolver el token (o `None` si las credenciales son
inválidas):

```python
# services/login.py (después)
class LoginService():
    def __init__(self, repo: UserRepositoryDep, jwt_service: JWTServiceDep):
        self.repo = repo
        self.jwt_service = jwt_service

    def login(self, email: str, pwd: str) -> str | None:
        user = self.repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(pwd, user.password):
            return None
        return self.jwt_service.create_access_token({"sub": user.email})
```

Y `api/login.py` deja de devolver el string fijo `"121456"`:

```python
# api/login.py (después)
@router.post("/login", response_model=LoginResponse)
def login(req: Login, service: LoginServiceDep) -> LoginResponse:
    token = service.login(req.email, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="User/password incorrect")
    return LoginResponse(msg="ok", token=token)
```

(`JWTServiceDep` seguiría el mismo patrón que ya existe en
`dependencies.py` para las otras dependencias, por ejemplo:
`JWTServiceDep = Annotated[JWTService, Depends(get_jwt_service)]`, donde
`get_jwt_service` construye el `JWTService` con la `secret_key` leída de la
configuración.)

---

## Paso 4 — Validar el token en cada request

Acá hay dos caminos posibles, y vale la pena entender por qué elegimos uno.

**Lo que hay hoy**: un middleware global, `CheckApikeyMW`
(`api/middlewares/check_apikey.py`), registrado en `main.py` con
`app.middleware("apikey")`. Corre para *todas* las requests salvo una lista
fija de excepciones (`/docs`, `/openapi.json`, `/login`), y solo sabe decir
"sí" o "no" — no tiene forma simple de pasarle a la función de la ruta
*quién* es el usuario autenticado.

**Lo recomendado para JWT**: una **dependency** de FastAPI, no un
middleware. Una dependency puede devolver el usuario ya resuelto, y
FastAPI se lo inyecta directamente a la función de la ruta — que es
exactamente lo que necesitamos ("dame el usuario autenticado", no solo "sí,
está autenticado"). En `dependencies.py` agregaríamos algo así:

```python
# dependencies.py (agregado)
from fastapi import Header, HTTPException
from model.users import UserDB


def get_current_user(
    authorization: Annotated[str, Header()],
    jwt_service: JWTServiceDep,
    repo: UserRepositoryDep,
) -> UserDB:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ")
    payload = jwt_service.decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = repo.get_by_email(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


CurrentUserDep = Annotated[UserDB, Depends(get_current_user)]
```

Notar que `repo.get_by_email(...)` ya existe hoy en
`repositories/users.py` — no hay que escribirlo de nuevo, solo reutilizarlo.

Y en `api/users.py`, reemplazaríamos la dependencia actual:

```python
# api/users.py (hoy)
def verify_api_key_header(x_api_key: Annotated[str, Header()]) -> str:
    return x_api_key

router = APIRouter(dependencies=[Depends(verify_api_key_header)], tags=["Users"])
```

por la nueva, que además de proteger la ruta resuelve el usuario real:

```python
# api/users.py (después)
router = APIRouter(dependencies=[Depends(get_current_user)], tags=["Users"])
```

(o, en un endpoint puntual que necesite saber quién es el usuario logueado,
usando `CurrentUserDep` como parámetro directamente, por ejemplo
`def get_me(user: CurrentUserDep) -> User: return user`.)

Con esto, `app.middleware("apikey")` en `main.py` (y la clase
`CheckApikeyMW` que lo respalda) quedarían **retirados**: ya no hace falta
una clave estática global, porque cada ruta protegida valida su propio
token vía dependency.

---

## Paso 5 — Probar el flujo de punta a punta

```bash
# 1. Login sin credenciales válidas → 401
curl -i -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mgomez@email.com","password":"incorrecta"}'

# 2. Login correcto → devuelve el token
curl -i -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mgomez@email.com","password":"123"}'
# { "msg": "ok", "token": "eyJhbGciOi..." }

# 3. Request protegida SIN token → 401
curl -i http://localhost:8000/user

# 4. Request protegida CON token → 200
curl -i http://localhost:8000/user \
  -H "Authorization: Bearer eyJhbGciOi..."

# 5. Token alterado o vencido → 401
curl -i http://localhost:8000/user \
  -H "Authorization: Bearer eyJhbGciOi...manipulado"
```

---

## Cierre — límites de este alcance

Esta guía cubre solo **access tokens**, a propósito, para mantener el primer
paso simple:

- No hay **refresh tokens**: cuando el token expira, el usuario tiene que
  volver a loguearse. Es un ejercicio natural para después: un segundo
  token, de vida más larga, que sirve únicamente para pedir un access token
  nuevo sin mandar la contraseña de nuevo.
- No hay forma de **revocar** un token antes de que expire (por ejemplo, al
  hacer logout) — con JWT "puro" eso requiere una lista negra de tokens en
  el servidor, que es otro tema en sí mismo.
- La `secret_key` **nunca** va al repo (ni hardcodeada, ni en un `.env`
  commiteado) — se pasa como variable de entorno en cada ambiente.

Con los pasos 1 a 5, sin embargo, ya tenemos lo esencial funcionando: login
real, contraseñas hasheadas, y cada request sabe exactamente qué usuario la
está haciendo.
