# ADR-001: Domain Model como patrón de lógica de negocio

**Estado:** Aceptada

## Contexto
CargoBox no es un CRUD: tiene una máquina de estados rígida y reglas que deben protegerse (BR012 evidencia, BR014 intentos, BR005 tarifa).

## Decisión
Usar **Domain Model** con DDD: agregado raíz `Paquete`, Value Objects inmutables y servicios de dominio (`CalculadoraTarifa`). Los métodos llevan nombres del negocio (`finalizar_entrega(evidencia)`).

## Alternativas consideradas
Transaction Script (reglas duplicadas en cada endpoint); Table Module (separa datos de comportamiento).

## Consecuencias
+ Reglas en un solo lugar y fáciles de probar. − Más capas y curva de aprendizaje (ya aceptado en U3).
