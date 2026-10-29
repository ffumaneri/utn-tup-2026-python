# TP: Sistema de Biblioteca (FastAPI + SQLModel)

## Objetivo
Construir una API REST para gestionar el catálogo de una biblioteca y sus préstamos. Hay que modelar entidades con relaciones y aplicar reglas de negocio con los códigos HTTP correctos.

## Modelo de datos

| Entidad | Campos |
|---|---|
| `Autor` | id, nombre, nacionalidad |
| `Libro` | id, titulo, isbn (único), stock (≥ 0), anio |
| `LibroAutor` | libro_id, autor_id (tabla intermedia) |
| `Socio` | id, nombre, email (único), activo |
| `Prestamo` | id, socio_id, libro_id, fecha_prestamo, fecha_vencimiento, fecha_devolucion (nullable), multa |

**Relaciones:**
- Libro N-N Autor.
- Préstamo N-1 Socio.
- Préstamo N-1 Libro.

## Endpoints mínimos

| Método | Ruta | Descripción |
|---|---|---|
| CRUD | `/autores`, `/libros`, `/socios` | Alta, baja, modificación y consulta |
| POST | `/libros/{id}/autores/{autor_id}` | Asocia un autor a un libro |
| GET | `/libros?disponibles=true` | Libros con stock > 0 |
| POST | `/prestamos` | Registra un préstamo |
| POST | `/prestamos/{id}/devolucion` | Registra la devolución |
| GET | `/socios/{id}/prestamos?activos=true` | Préstamos activos del socio |

## Reglas de negocio

| # | Regla | Error |
|---|---|---|
| 1 | Un socio no puede tener más de 3 préstamos activos | 409 |
| 2 | No se presta un libro sin stock; al prestar se descuenta 1 | 409 |
| 3 | Un socio inactivo no puede pedir préstamos | 403 |
| 4 | El plazo es de 14 días; `fecha_vencimiento = fecha_prestamo + 14 días` | n/a |
| 5 | Al devolver se repone el stock y se calcula la multa: $100 × días de atraso (0 si llegó a tiempo) | n/a |
| 6 | No se puede devolver un préstamo ya devuelto | 409 |
| 7 | Recurso inexistente | 404 |
| 8 | ISBN o email duplicado | 409 |

## Etapas sugeridas
1. **CRUD y modelos:** SQLModel, sesión de base de datos, routers por entidad.
2. **Relaciones:** N-N Libro/Autor y respuestas que incluyan los autores del libro.
3. **Préstamos:** reglas de negocio en una capa `services`, no en el router.
4. **Tests:** pytest con base en memoria, cobertura ≥ 80 %.
5. **Opcional:** roles `bibliotecario` y `socio`. Solo el bibliotecario administra el catálogo, y el socio ve únicamente sus préstamos.

## Entrega
- Repositorio con README (cómo correr y cómo testear).
- Estructura sugerida: `models/`, `routers/`, `services/`, `tests/`.
- Tests que cubran cada regla de negocio, tanto el caso feliz como el de error.

## Rúbrica (100 pts)

| Criterio | Pts |
|---|---|
| Modelo y relaciones correctas | 20 |
| Endpoints y códigos HTTP | 20 |
| Reglas de negocio | 25 |
| Tests y cobertura | 20 |
| Estructura y claridad del código | 15 |
