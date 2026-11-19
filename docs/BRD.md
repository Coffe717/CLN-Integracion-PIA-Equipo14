# CargoBox · BRD (Business Requirements Document)
Refinado desde U2/U3 para el PIA. Original: `analisis/BRD_original.pdf`.
Equipo 14 · UANL-FIME · Componentes de Lógica de Negocios · Grupo 002.

## 1. Contexto
CargoBox es una empresa logística de envíos nacionales. El precio de cada paquete depende de dimensiones, peso, destino y nivel de servicio. Cada envío tiene una **guía única** para rastrearlo en toda la red.

## 2. Problemas y oportunidades
| ID | Problema | Oportunidad |
|----|----------|-------------|
| BR001 | Llamadas al cliente por falta de estados | Rastreo en tiempo real visible al cliente |
| BR002 | Eventos incompletos / paquetes detenidos | Alertas por inactividad (24/48 h) |
| BR003 | Incidencias en ruta difíciles de escalar | Tickets a Atención al cliente |
| BR004 | Evidencias de entrega dispersas | Evidencia digital ligada a la guía |

## 3. Stakeholders
Remitente · Empleado de sucursal · Centro de distribución · Repartidor · Destinatario · Atención al cliente · Supervisor de operaciones · Auditor de calidad / Legal.

## 4. Alcance
**Dentro:** guías únicas y tarifa automática · estados del paquete · evidencia obligatoria · excepciones (ausente, daño, dirección, rechazo) · alertas · logística inversa.
**Fuera:** contabilidad y facturación fiscal · cobros con tarjeta · flotilla de vehículos · nóminas y comisiones.

## 5. Necesidades (requerimientos de negocio)
| ID | Necesidad | Dónde se implementa |
|----|-----------|---------------------|
| BR005 | Tarifa calculada por parámetros (dimensiones, peso, destino, servicio) | `domain/tabulador.py` |
| BR006 | Guía única al recibir en sucursal | `Paquete.recibir`, `GeneradorGuia` |
| BR007 | Estado **Recibido** al capturar datos | `Paquete.recibir` |
| BR008 | **Clasificado** al escanear en CD | `Paquete.clasificar` |
| BR009 | **En tránsito** entre instalaciones | `ManifiestoViaje.despachar` |
| BR010 | **Centro destino** al llegar a la ciudad final | `Paquete.marcar_centro_destino` |
| BR011 | **En reparto** al cargar la unidad | `RutaReparto.iniciar` |
| BR012 | Evidencia obligatoria para **Entregado** | `Paquete.finalizar_entrega` |
| BR013 | Excepción "dirección incorrecta" | `Paquete.pausar_por_direccion_incorrecta` |
| BR014 | "Destinatario ausente": 2.º intento automático; 3.º con autorización | `Paquete.registrar_ausencia` |

## 6. Restricciones
- El precio **no se modifica a mano**: lo calcula el sistema.
- **Entregado** está bloqueado sin evidencia.
- Tras "ausente" solo se programa un 2.º intento automático; el 3.º requiere autorización.
- Incidencias mayores (daño/pérdida) las resuelve **solo Atención al cliente**.

## 7. Supuestos
Terminales con internet · operación solo en México en MXN · el ruteo es un sistema externo.

## 8. Criterios de éxito
Menos llamadas por dudas de rastreo · 100 % de evidencias digitales · detección proactiva de paquetes estancados.

## 9. Reglas del tabulador (decisión de refinamiento)
- Peso facturable = mayor entre peso real y peso volumétrico (largo×ancho×alto ÷ 5000).
- Precio = base del tramo × factor de zona × factor de servicio.

| Peso facturable (kg) | ≤1 | ≤3 | ≤5 | ≤10 | ≤20 | ≤30 | ≤70 |
|---|---|---|---|---|---|---|---|
| Base (MXN) | 60 | 90 | 120 | 150 | 230 | 330 | 520 |

Zona: local ×1.00 · regional ×1.25 · nacional ×1.60. Servicio: Estándar ×1.00 · Exprés ×1.50.
Entrega: Estándar 2/4/6 días · Exprés 1/2/3 días (local/regional/nacional).
Ejemplo CP-07: 5 kg, 30×30×30 cm → volumétrico 5.4 kg → tramo ≤10 → **$150.00 MXN**.
