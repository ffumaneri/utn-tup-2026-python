# Trabajo Práctico: ABM de Usuarios con FastAPI + ABM propio

## Objetivo

Completar y extender la API de ejemplo vista en clase (`clase-fastapi`) para
tener un ABM (Alta, Baja, Modificación) completo de usuarios, y luego
replicar ese mismo patrón para crear el ABM de una entidad propia.

## Parte 1 — Completar el ABM de usuarios

Sobre el proyecto `clase-fastapi` (el que se armó en clase), agregar/completar
los siguientes endpoints sobre la entidad `Usuario`:

- **Eliminar** un usuario por id (`DELETE`).
- **Modificar** los datos de un usuario existente (`PUT` o `PATCH`).
- **Buscar/listar usuarios filtrando por estado**: activos, inactivos, o
  todos (por ejemplo vía un query param `is_active`).

Los endpoints ya existentes de alta y listado se pueden mantener o mejorar,
pero el foco de esta parte es completar lo que falta.

## Parte 2 — ABM de una entidad propia

Elegir una entidad distinta a `Usuario`, con **5 campos**, y construir un
ABM/CRUD completo (crear, listar, obtener por id, modificar, eliminar y
buscar/filtrar por algún campo relevante), siguiendo el mismo patrón usado
para usuarios (modelos con Pydantic, router de FastAPI, almacenamiento en
memoria).

Por ejemplo, la entiedad "Auto" con id, marca, modelo, número de chasis y año.
> IMPORTANTE: No usar la entidad Auto dada de ejemplo.

## Entrega

- Un link a un repositorio (GitHub o similar) con el código de la
  aplicación funcionando.
- Un `README.md` con instrucciones claras de cómo:
  - Instalar dependencias y levantar la aplicación.
  - Acceder a la documentación interactiva (Swagger) en `/docs` para poder
    probar todos los endpoints.

## Plazo

La entrega debe realizarse **antes de finalizar el cuatrimestre**, para
poder obtener la regularidad de la materia.
