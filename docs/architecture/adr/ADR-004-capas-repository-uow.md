# ADR-004: Capas + Repository + Unit of Work (puertos y adaptadores)

**Estado:** Aceptada

## Contexto
El dominio no debe depender de la base de datos ni del framework web (DIP).

## Decisión
Capas `domain → application → infrastructure/api`. La aplicación define puertos (`IPaqueteRepository`, `IUnitOfWork`...) y la infraestructura los implementa (SQL y memoria). Cada caso de uso es una transacción.

## Alternativas consideradas
Acceder a SQLite/Flask desde las entidades; usar un ORM completo.

## Consecuencias
+ Pruebas rápidas en memoria y mismas pruebas sobre SQL. − Mapeo manual agregado ↔ JSON.
