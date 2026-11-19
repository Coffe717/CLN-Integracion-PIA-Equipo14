# ADR-005: Eventos de dominio en proceso

**Estado:** Aceptada

## Contexto
Otros módulos (avisos a Atención, supervisor) deben reaccionar sin acoplarse al agregado.

## Decisión
El agregado acumula eventos (`pull_events`); el servicio los publica tras guardar; `ManejadorNotificaciones` crea avisos. 24 eventos definidos.

## Alternativas consideradas
Llamar directamente al notificador desde el dominio; broker de mensajes externo.

## Consecuencias
+ Dominio desacoplado. − Los eventos viven en memoria (sin entrega garantizada).
