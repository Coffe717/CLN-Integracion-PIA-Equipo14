# Decisiones técnicas, patrones y SOLID

## Capas
```
api (Flask: rutas, OpenAPI, UI)  →  application (servicios, puertos, eventos)  →  domain (reglas)
infrastructure (SQL, memoria, semilla)  implementa los puertos de application
```
Regla: las flechas solo apuntan hacia el dominio. El dominio no importa Flask ni SQL.

## Patrones usados y por qué
| Patrón | Dónde | Justificación |
|---|---|---|
| Domain Model / DDD | `domain/` | Reglas complejas y estados (ADR-001) |
| Aggregate Root | `Paquete`, `Incidencia`, `ManifiestoViaje`, `RutaReparto`, `TabuladorTarifas` | Consistencia por agregado |
| Value Object | `Peso`, `Dimensiones`, `Dinero`, `Tarifa`, `GuiaRastreo`, `EvidenciaRecepcion`… | Datos inválidos nunca existen (CP-08) |
| State Machine | `estado.py` | Transiciones controladas (ADR-002) |
| Specification | `especificaciones.py` | Reglas combinables AND/OR/NOT (ADR-003) |
| Domain Service | `CalculadoraTarifa` | Cálculo que no pertenece a una entidad |
| Domain Events + Observer | `eventos.py`, `PublicadorEventos` | Desacoplar avisos (ADR-005) |
| Service Layer | `application/servicios.py` | Un caso de uso = una transacción |
| Repository + Unit of Work | `puertos.py`, `repositorios_sql.py`, `memoria.py` | Aislar persistencia (ADR-004) |
| Composition Root | `infrastructure/composicion.py` | Un único lugar arma las dependencias |

## SOLID (con evidencia)
- **S**: `CalculadoraTarifa` solo calcula; `MaquinaEstados` solo valida transiciones; los servicios solo orquestan.
- **O**: nueva regla = nueva `Specification` o nuevo tramo del tabulador, sin tocar código existente.
- **L**: repositorios SQL y en memoria son intercambiables; las mismas pruebas corren con ambos (`fixture contenedor`).
- **I**: puertos pequeños y separados (`IPaqueteRepository`, `INotificador`, `IGeneradorGuia`…).
- **D**: los servicios dependen de interfaces (`application/puertos.py`), no de SQLite ni Flask.

## Contrato HTTP
200/201 éxito · 400 solicitud mal formada · 403 rol no permitido · 404 no existe · 409 conflicto de estado o regla (transición inválida, 3.er intento) · 422 dato o validación (evidencia obligatoria, peso negativo).

## Diferencias con el paquete de datos del docente
`INSTRUCCIONES_ALUMNO.txt` propone un modelo de pruebas genérico (RECIBIDO→CLASIFICADO→EN_TRANSITO→ENTREGADO, `puede_procesarse`, `beneficio_referencia`). Como indica el propio documento, **la implementación se deriva del BRD propio**: se usan los 13 estados del BRD/BPMN y sus reglas. De los datos se reutiliza `actores.csv` (40 remitentes, cargados como semilla). `beneficio_referencia` no se implementa porque el BRD prohíbe modificar el precio manualmente.

## Diagramas (draw.io)
Abrir con https://app.diagrams.net o la extensión de VS Code:
`diagramas/01-dominio-ddd.drawio` · `02-clases-uml.drawio` · `03-maquina-estados.drawio` · `04-secuencia-entrega.drawio` · `05-arquitectura-capas.drawio`. El BPMN del equipo está en `../analisis/BPMN_original.pdf`.
