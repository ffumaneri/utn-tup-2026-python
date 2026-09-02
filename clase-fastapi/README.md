# Clase FastAPI

Clase para aprender **FastAPI** y **Pydantic**.

## Crear el entorno virtual (venv)

Desde esta carpeta (`clase-fastapi`):

```bash
python3 -m venv .venv
```

Activar el entorno virtual:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

## Instalar los requerimientos

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
fastapi dev main.py
```

La API quedará disponible en `http://127.0.0.1:8000` y la documentación interactiva en `http://127.0.0.1:8000/docs`.

## Lint y chequeo de tipos

El proyecto incluye configuración local para dos herramientas:

- **[`setup.cfg`](./setup.cfg)**: configuración de [`pycodestyle`](https://pycodestyle.pycqa.org/) (chequeo de estilo PEP 8). Define `max-line-length = 79` y excluye `.venv` y `__pycache__` del análisis.
- **[`pyrightconfig.json`](./pyrightconfig.json)**: configuración de [`pyright`](https://microsoft.github.io/pyright/) (chequeo de tipos). Apunta al entorno virtual local (`.venv`) para resolver las dependencias instaladas y excluye `.venv` y `__pycache__`.

`pyright` ya está incluido en `requirements.txt`. `pycodestyle` no, así que hay que instalarlo aparte.

Con el entorno virtual activado, correr:

```bash
pip install pycodestyle
python -m pycodestyle .
```

```bash
pyright
```
