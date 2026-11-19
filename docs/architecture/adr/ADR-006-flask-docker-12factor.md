# ADR-006: Flask + SQLite/PostgreSQL + Docker Compose (12-Factor)

**Estado:** Aceptada

## Contexto
Se necesita API REST documentada, base de datos, entorno reproducible y despliegue simple.

## Decisión
Flask (API + UI estática), OpenAPI 3 servida en `/openapi.json` y Swagger UI en `/docs`. Configuración por variables de entorno. SQLite local y PostgreSQL en Compose/producción. Despliegue en Render (`render.yaml`).

## Alternativas consideradas
FastAPI + SQLAlchemy; frameworks SPA para la UI.

## Consecuencias
+ Pocas dependencias y arranque inmediato. − SQL escrito a mano (sencillo y portable).
