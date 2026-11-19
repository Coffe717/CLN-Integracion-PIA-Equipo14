# ADR-003: Patrón Specification para reglas combinables

**Estado:** Aceptada

## Contexto
Reglas como 'estancado = NO terminal Y sin cambios > umbral' o 'requiere autorización = intentos agotados Y NO autorizado' se combinan y reutilizan.

## Decisión
Clase base `Specification` con `&`, `|` y `~` (AND/OR/NOT). Specs de ejemplo: `PaqueteEstancadoSpec`, `RequiereAutorizacionTercerIntentoSpec`, `PuedeEnviarSpec`.

## Alternativas consideradas
Funciones sueltas con `if`; consultas SQL con la regla incrustada.

## Consecuencias
+ Reglas con nombre de negocio y composables. − Una clase por regla.
