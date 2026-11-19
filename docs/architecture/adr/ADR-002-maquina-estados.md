# ADR-002: Máquina de estados explícita

**Estado:** Aceptada

## Contexto
El envío pasa por 13 estados y cualquier salto indebido (p. ej. Recibido → Entregado) rompe el negocio.

## Decisión
Tabla `TRANSICIONES` + clase `MaquinaEstados`. Todo cambio de estado pasa por `transicionar`; si no está permitido se lanza `TransicionEstadoInvalidaException`.

## Alternativas consideradas
Banderas booleanas en `Paquete`; `if` anidados en cada método; librería externa de FSM.

## Consecuencias
+ Una sola fuente de verdad, fácil de dibujar y probar (CP-03). − Hay que mantener la tabla al agregar estados.
