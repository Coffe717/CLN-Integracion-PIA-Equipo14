# Glosario de dominio (lenguaje ubicuo)
Original: `analisis/Glosario_original.pdf`. Estos mismos nombres se usan en el código.

| Término | Significado | En el código |
|---|---|---|
| Guía | Código único de rastreo `CB-XXXXXXXXXX` | `GuiaRastreo` |
| Paquete | Envío con ciclo de vida y rastreo | `Paquete` (agregado raíz) |
| Nivel de servicio | Estándar o Exprés: define costo y tiempo | `NivelServicio` |
| Tabulador | Reglas que calculan la tarifa; sin edición manual | `TabuladorTarifas`, `CalculadoraTarifa` |
| Manifiesto de viaje | Agrupa paquetes de un traslado entre ciudades | `ManifiestoViaje` |
| Ruta de reparto | Paquetes de un repartidor en una jornada | `RutaReparto` |
| Evidencia de recepción | Firma y/o foto de quien recibe; obligatoria para entregar | `EvidenciaRecepcion` |
| Intento de entrega | Visita al domicilio; máximo 2 automáticos | `intentos_fallidos` |
| Excepción operativa | Ausente, dirección incorrecta, rechazo, daño/pérdida | métodos de `Paquete` |
| Incidencia / Ticket | Registro que atiende Atención al cliente | `Incidencia` |
| Alerta de inactividad | Aviso por paquete sin cambios más allá del umbral | `PaqueteEstancadoSpec` |
| Umbral | Horas máximas sin actualización | `UMBRAL_HORAS` |

**Estados:** Recibido · Clasificado · En tránsito · Centro destino · En reparto · Entregado · Segundo intento pendiente · Retenido en sucursal · Dirección incorrecta · Retenido por incidencia · Rechazado - En proceso de devolución · Devuelto a origen · Cancelado.
