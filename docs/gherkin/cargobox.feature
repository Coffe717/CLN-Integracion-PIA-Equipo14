# language: es
Característica: Gestión de envíos CargoBox

  @HU-01 @BR005
  Escenario: HU-01 Cálculo estricto por sistema
    Dado que la terminal tiene peso, dimensiones, destino y nivel de servicio capturados
    Cuando solicito la cotización
    Entonces el sistema aplica el tabulador y muestra la tarifa sin permitir editar el precio

  @HU-02 @BR006
  Escenario: HU-02 Guía y estado inicial
    Dado que la tarifa fue calculada
    Cuando confirmo la recepción
    Entonces el sistema genera una guía CB-XXXXXXXXXX y asigna el estado Recibido

  @HU-03 @BR008
  Escenario: HU-03 Escaneo de clasificación
    Dado que un paquete en estado Recibido llega al centro
    Cuando escaneo su guía
    Entonces el estado cambia a Clasificado con fecha, hora e instalación

  @HU-04 @BR009
  Escenario: HU-04 Salida del manifiesto
    Dado que paquetes Clasificados cargados al transporte
    Cuando genero la salida del manifiesto
    Entonces todos los paquetes del manifiesto quedan En tránsito

  @HU-05 @BR010
  Escenario: HU-05 Arribo a destino
    Dado que una unidad con paquetes En tránsito llega
    Cuando registro la llegada
    Entonces el estado cambia a Centro destino

  @HU-06 @BR011
  Escenario: HU-06 Carga en tiempo real
    Dado que paquetes en Centro destino
    Cuando inicio mi ruta diaria
    Entonces el estado cambia a En reparto y se ve de inmediato en el rastreo

  @HU-07 @BR012
  Escenario: HU-07 Bloqueo por falta de evidencia
    Dado que un paquete En reparto
    Cuando intento finalizar la entrega sin firma ni foto
    Entonces el sistema bloquea la entrega e indica que la evidencia es obligatoria

  @HU-08 @BR013
  Escenario: HU-08 Pausa y ticket
    Dado que no localizo la dirección de un paquete En reparto
    Cuando elijo Dirección incorrecta
    Entonces se pausa la entrega y llega un ticket a Atención al cliente

  @HU-09 @BR014
  Escenario: HU-09 2.º intento automático
    Dado que primera visita sin encontrar al destinatario
    Cuando marco Destinatario ausente
    Entonces el estado es Segundo intento pendiente y se reagenda

  @HU-10 @BR003
  Escenario: HU-10 Escalamiento
    Dado que un paquete con daño estructural grave
    Cuando elijo Reportar daño/incidencia mayor
    Entonces la entrega se impide y el control pasa a Atención al cliente

  @HU-11 @BR002
  Escenario: HU-11 Detección de inactividad
    Dado que un paquete sin cambios por más del umbral (24/48 h)
    Cuando se ejecuta el monitoreo
    Entonces aparece una alerta con guía, último estado y horas de estancamiento

  @HU-12 @BR001
  Escenario: HU-12 Centralización de información
    Dado que un cliente llama a atención
    Cuando ingreso su número de guía
    Entonces veo la línea de tiempo completa, la evidencia y las incidencias

  @HU-13 @Alcance
  Escenario: HU-13 Proceso de retorno
    Dado que el destinatario rechaza el paquete
    Cuando capturo el motivo de rechazo
    Entonces el estado es Rechazado - En proceso de devolución y regresa a origen

  @HU-14 @BR004
  Escenario: HU-14 Acceso a evidencia
    Dado que una guía en estado Entregado
    Cuando busco el registro en el repositorio central
    Entonces veo firma, fotografía y fecha-hora de la entrega

  @HU-15 @BR005
  Escenario: HU-15 Ajuste por nivel de servicio
    Dado que un paquete con peso y medidas fijas
    Cuando cambio de Estándar a Exprés
    Entonces el sistema recalcula la tarifa y ajusta la promesa de entrega

  @BR012
  Escenario: CP-02 sin evidencia
    Dado que un paquete En reparto
    Cuando el repartidor finaliza sin evidencia (nula)
    Entonces se lanza EvidenciaObligatoriaException y sigue En reparto

  @BR014
  Escenario: CP-05 tercer intento sin autorización
    Dado que un paquete con dos intentos fallidos y sin autorización
    Cuando el repartidor marca ausente por tercera vez
    Entonces se lanza TercerIntentoNoAutorizadoException

  @BR014
  Escenario: CP-06 tercer intento autorizado
    Dado que un paquete con dos intentos fallidos y autorización de supervisor
    Cuando el repartidor marca ausente por tercera vez
    Entonces el estado es Retenido en sucursal

