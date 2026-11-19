# Historias de usuario (15) con criterios de aceptación Gherkin

Refinadas desde el trabajo de la Unidad 2. Cada historia indica su regla de negocio (BR) y dónde vive en el código.

## HU-01 · Cálculo de tarifas automatizado
**Regla:** BR005  
**Como** Empleado de sucursal, **quiero** registrar peso, dimensiones, destino y nivel de servicio, **para que** se calcule la tarifa exacta sin intervención manual.  
**Implementación:** CalculadoraTarifa · POST /cotizaciones · tests: CP-07, CP-08

```gherkin
Escenario: Cálculo estricto por sistema
  Dado que la terminal tiene peso, dimensiones, destino y nivel de servicio capturados
  Cuando solicito la cotización
  Entonces el sistema aplica el tabulador y muestra la tarifa sin permitir editar el precio
```

## HU-02 · Guía única e inicio en Recibido
**Regla:** BR006, BR007  
**Como** Empleado de sucursal, **quiero** confirmar la recepción del paquete, **para que** se genere una guía única y el estado inicial sea Recibido.  
**Implementación:** Paquete.recibir · POST /paquetes

```gherkin
Escenario: Guía y estado inicial
  Dado que la tarifa fue calculada
  Cuando confirmo la recepción
  Entonces el sistema genera una guía CB-XXXXXXXXXX y asigna el estado Recibido
```

## HU-03 · Clasificado en Centro de Distribución
**Regla:** BR008, BR002  
**Como** Operador de Centro de Distribución, **quiero** escanear la guía, **para que** el paquete pase a Clasificado con fecha, hora e instalación.  
**Implementación:** Paquete.clasificar · POST /paquetes/{guia}/clasificar

```gherkin
Escenario: Escaneo de clasificación
  Dado que un paquete en estado Recibido llega al centro
  Cuando escaneo su guía
  Entonces el estado cambia a Clasificado con fecha, hora e instalación
```

## HU-04 · Movimiento entre ciudades (En tránsito)
**Regla:** BR009, BR002  
**Como** Operador de Logística, **quiero** despachar el manifiesto de viaje, **para que** los paquetes pasen a En tránsito.  
**Implementación:** ManifiestoViaje.despachar · POST /manifiestos

```gherkin
Escenario: Salida del manifiesto
  Dado que paquetes Clasificados cargados al transporte
  Cuando genero la salida del manifiesto
  Entonces todos los paquetes del manifiesto quedan En tránsito
```

## HU-05 · Recepción en ciudad final (Centro destino)
**Regla:** BR010, BR002  
**Como** Operador de Centro Destino, **quiero** registrar la llegada de la unidad, **para que** los paquetes pasen a Centro destino.  
**Implementación:** ManifiestoViaje.arribar · POST /manifiestos/{id}/arribo

```gherkin
Escenario: Arribo a destino
  Dado que una unidad con paquetes En tránsito llega
  Cuando registro la llegada
  Entonces el estado cambia a Centro destino
```

## HU-06 · Asignación a ruta local (En reparto)
**Regla:** BR011, BR001  
**Como** Repartidor, **quiero** cargar mis paquetes y iniciar ruta, **para que** el cliente vea En reparto en tiempo real.  
**Implementación:** RutaReparto.iniciar · POST /rutas

```gherkin
Escenario: Carga en tiempo real
  Dado que paquetes en Centro destino
  Cuando inicio mi ruta diaria
  Entonces el estado cambia a En reparto y se ve de inmediato en el rastreo
```

## HU-07 · Cierre de entrega con evidencia obligatoria
**Regla:** BR012, BR004  
**Como** Repartidor, **quiero** capturar firma o foto del receptor, **para que** se desbloquee el estado Entregado.  
**Implementación:** Paquete.finalizar_entrega · tests: CP-01, CP-02, CP-03

```gherkin
Escenario: Bloqueo por falta de evidencia
  Dado que un paquete En reparto
  Cuando intento finalizar la entrega sin firma ni foto
  Entonces el sistema bloquea la entrega e indica que la evidencia es obligatoria
```

## HU-08 · Excepción: dirección incorrecta
**Regla:** BR013, BR003  
**Como** Repartidor, **quiero** registrar Dirección incorrecta, **para que** se pause la entrega y se avise a Atención al cliente.  
**Implementación:** IncidenciaService.reportar_direccion_incorrecta

```gherkin
Escenario: Pausa y ticket
  Dado que no localizo la dirección de un paquete En reparto
  Cuando elijo Dirección incorrecta
  Entonces se pausa la entrega y llega un ticket a Atención al cliente
```

## HU-09 · Destinatario ausente: segundo intento
**Regla:** BR014  
**Como** Repartidor, **quiero** registrar que el destinatario no estaba, **para que** el sistema reagende el segundo intento y exija autorización para el tercero.  
**Implementación:** Paquete.registrar_ausencia · tests: CP-04, CP-05, CP-06

```gherkin
Escenario: 2.º intento automático
  Dado que primera visita sin encontrar al destinatario
  Cuando marco Destinatario ausente
  Entonces el estado es Segundo intento pendiente y se reagenda
```

## HU-10 · Escalamiento de incidencias mayores
**Regla:** BR003  
**Como** Repartidor, **quiero** reportar daño o pérdida, **para que** el caso pase a Atención al cliente sin resolverlo en campo.  
**Implementación:** Paquete.retener_por_incidencia · Incidencia.resolver

```gherkin
Escenario: Escalamiento
  Dado que un paquete con daño estructural grave
  Cuando elijo Reportar daño/incidencia mayor
  Entonces la entrega se impide y el control pasa a Atención al cliente
```

## HU-11 · Alertas por rastreos sin actualización
**Regla:** BR002  
**Como** Supervisor de Operaciones, **quiero** recibir alertas de paquetes detenidos, **para que** detecte estancamientos antes de que el cliente reclame.  
**Implementación:** PaqueteEstancadoSpec · GET /alertas

```gherkin
Escenario: Detección de inactividad
  Dado que un paquete sin cambios por más del umbral (24/48 h)
  Cuando se ejecuta el monitoreo
  Entonces aparece una alerta con guía, último estado y horas de estancamiento
```

## HU-12 · Consulta de rastreo completo
**Regla:** BR001, BR004  
**Como** Agente de Atención al Cliente, **quiero** ver el historial y evidencias de una guía, **para que** resuelva rápido las llamadas.  
**Implementación:** ConsultaRastreoService · GET /paquetes/{guia}

```gherkin
Escenario: Centralización de información
  Dado que un cliente llama a atención
  Cuando ingreso su número de guía
  Entonces veo la línea de tiempo completa, la evidencia y las incidencias
```

## HU-13 · Rechazo del paquete
**Regla:** Alcance: excepciones  
**Como** Repartidor, **quiero** registrar Paquete rechazado, **para que** inicie la devolución a la sucursal de origen.  
**Implementación:** Paquete.registrar_rechazo · POST /paquetes/{guia}/rechazo

```gherkin
Escenario: Proceso de retorno
  Dado que el destinatario rechaza el paquete
  Cuando capturo el motivo de rechazo
  Entonces el estado es Rechazado - En proceso de devolución y regresa a origen
```

## HU-14 · Consulta digital de evidencias
**Regla:** BR004  
**Como** Auditor de Calidad / Abogado Interno, **quiero** consultar las evidencias vinculadas a cada guía, **para que** respalde legalmente las entregas.  
**Implementación:** GET /paquetes/{guia}/evidencia · pestaña Auditoría

```gherkin
Escenario: Acceso a evidencia
  Dado que una guía en estado Entregado
  Cuando busco el registro en el repositorio central
  Entonces veo firma, fotografía y fecha-hora de la entrega
```

## HU-15 · Selección de nivel de servicio
**Regla:** BR005  
**Como** Remitente, **quiero** elegir Estándar o Exprés al cotizar, **para que** ajuste costo y tiempo de entrega.  
**Implementación:** NivelServicio · TabuladorTarifas

```gherkin
Escenario: Ajuste por nivel de servicio
  Dado que un paquete con peso y medidas fijas
  Cuando cambio de Estándar a Exprés
  Entonces el sistema recalcula la tarifa y ajusta la promesa de entrega
```

## Escenarios adicionales (casos CP de la tabla del PIA)

```gherkin
Escenario: CP-02 sin evidencia
  Dado que un paquete En reparto
  Cuando el repartidor finaliza sin evidencia (nula)
  Entonces se lanza EvidenciaObligatoriaException y sigue En reparto

Escenario: CP-05 tercer intento sin autorización
  Dado que un paquete con dos intentos fallidos y sin autorización
  Cuando el repartidor marca ausente por tercera vez
  Entonces se lanza TercerIntentoNoAutorizadoException

Escenario: CP-06 tercer intento autorizado
  Dado que un paquete con dos intentos fallidos y autorización de supervisor
  Cuando el repartidor marca ausente por tercera vez
  Entonces el estado es Retenido en sucursal

```
