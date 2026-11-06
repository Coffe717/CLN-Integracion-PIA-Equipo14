## 1. Contexto del Negocio
CargoBox es una empresa logística que requiere un sistema para asegurar el cálculo automatizado de tarifas, la trazabilidad ininterrumpida de los paquetes, el control de incidencias y la vinculación obligatoria de evidencias digitales en la entrega.

## 2. Glosario de Dominio (Lenguaje Ubicuo)
El sistema utiliza un lenguaje ubicuo para alinear al equipo técnico y al negocio:
* **Paquete (Aggregate Root):** Límite de consistencia principal que controla el ciclo de vida del envío, su historial de rastreo y los intentos de entrega.
* **Incidencia (Aggregate Root):** Registro para dar seguimiento a problemas operativos (dirección incorrecta, daño, pérdida) asignado a Atención al Cliente.
* **Manifiesto de Viaje (Aggregate Root):** Documento que agrupa guías de una unidad interurbana para su despacho y arribo.
* **Ruta de Reparto (Aggregate Root):** Colección de guías asignadas a un repartidor durante una jornada laboral.
* **Tabulador de Tarifas (Aggregate Root):** Contiene las reglas de precio basadas en peso, volumen, zona y nivel de servicio.
* **Guía de Rastreo (Value Object):** Código alfanumérico único que identifica al paquete.
* **Evidencia de Recepción (Value Object):** Comprobante digital compuesto por firma, fotografía y fecha/hora de la entrega.

## 3. User Stories (Gherkin)
---

### Historia 1: Cálculo de tarifas automatizado
* **Requerimiento asignado:** BR005[cite: 58]
* **Restricción:** El precio no puede modificarse manualmente[cite: 58].
* **Descripción:** Como Empleado de sucursal, quiero registrar el peso, dimensiones, destino y nivel de servicio de un paquete en el sistema, para que se calcule la tarifa exacta sin intervención manual[cite: 58].

**Criterio de Aceptación 1 (Cálculo estricto por sistema):**
* **Dado** que el empleado ha capturado las dimensiones, el peso, el destino y el nivel de servicio en la terminal de sucursal,[cite: 58]
* **Cuando** solicita la cotización del paquete,[cite: 58]
* **Entonces** el sistema aplica el tabulador automático y muestra la tarifa sin permitir la edición o modificación manual del precio final[cite: 58].

---

### Historia 2: Generación de guía única e inicio en estado "Recibido"
* **Requerimiento asignado:** BR006, BR007[cite: 58]
* **Necesidad:** Recepción en sucursal[cite: 58].
* **Descripción:** Como Empleado de sucursal, quiero concretar la recepción del paquete en el sistema, para generar una guía única rastreable y asignar automáticamente el estado inicial "Recibido"[cite: 58].

**Criterio de Aceptación 1 (Generación de guía y estado inicial):**
* **Dado** que la tarifa del envío ha sido calculada e ingresada al flujo de pago,[cite: 58]
* **Cuando** el empleado confirma la recepción del paquete,[cite: 58]
* **Entonces** el sistema genera un código de guía única de rastreo nacional y le asigna inmediatamente el estado "Recibido"[cite: 58].

---

### Historia 3: Cambio de estado a "Clasificado" en Centro de Distribución
* **Requerimiento asignado:** BR008, BR002[cite: 59]
* **Necesidad:** Procesamiento en centros de distribución[cite: 59].
* **Descripción:** Como Operador del Centro de Distribución, quiero escanear la guía del paquete ingresado, para cambiar su estado a "Clasificado" y mantener la visibilidad operativa en la red[cite: 59].

**Criterio de Aceptación 1 (Escaneo de clasificación):**
* **Dado** que el paquete ingresa al centro de distribución en estado "Recibido",[cite: 59]
* **Cuando** el operador escanea el código de barras de la guía en el área de clasificación,[cite: 59]
* **Entonces** el sistema actualiza el estado del paquete a "Clasificado" con fecha, hora e identificación de la instalación[cite: 59].

---

### Historia 4: Registro de movimientos entre ciudades ("En tránsito")
* **Requerimiento asignado:** BR009, BR002[cite: 59]
* **Necesidad:** Trazabilidad entre instalaciones[cite: 59].
* **Descripción:** Como Operador de Logística, quiero escanear los paquetes al despachar la unidad de transporte interurbano, para reflejar el estado "En tránsito" durante los trayectos entre instalaciones o ciudades[cite: 59].

**Criterio de Aceptación 1 (Actualización de estado a en tránsito):**
* **Dado** que los paquetes han finalizado su etapa de clasificación y son cargados al transporte principal,[cite: 59]
* **Cuando** el operador genera la salida del manifiesto de viaje,[cite: 59]
* **Entonces** el sistema cambia el estado de todos los paquetes vinculados a "En tránsito"[cite: 59].

---

### Historia 5: Recepción en ciudad final ("Centro Destino")
* **Requerimiento asignado:** BR010, BR002[cite: 59]
* **Necesidad:** Control de arribo final[cite: 59].
* **Descripción:** Como Operador del Centro de Distribución Destino, quiero registrar la llegada de la unidad interurbana, para marcar los paquetes recibidos con el estado "Centro destino"[cite: 59].

**Criterio de Aceptación 1 (Escaneo de arribo a destino):**
* **Dado** que una unidad ingresa a la instalación de la ciudad final con paquetes "En tránsito",[cite: 59]
* **Cuando** el personal escanea la recepción de la guía en la bahía de llegada,[cite: 59]
* **Entonces** el sistema actualiza de forma inmediata el estado del envío a "Centro destino"[cite: 59].

---

### Historia 6: Asignación a ruta local ("En reparto")
* **Requerimiento asignado:** BR011, BR001[cite: 60]
* **Necesidad:** Notificación en tiempo real al cargar la unidad[cite: 60].
* **Descripción:** Como Repartidor, quiero escanear los paquetes al cargarlos en mi unidad de entrega, para actualizar su estado en tiempo real a "En reparto" y reducir llamadas a atención al cliente[cite: 60].

**Criterio de Aceptación 1 (Carga en tiempo real):**
* **Dado** que los paquetes se encuentran en el "Centro destino",[cite: 60]
* **Cuando** el repartidor los escanea desde su terminal móvil e inicia la ruta diaria,[cite: 60]
* **Entonces** el sistema actualiza automáticamente el estado a "En reparto" y lo hace visible de forma inmediata en el rastreo del cliente[cite: 60].

---

### Historia 7: Cierre de entrega con evidencia digital obligatoria
* **Requerimiento asignado:** BR012, BR004[cite: 60]
* **Restricción:** Estado "Entregado" bloqueado sin evidencia[cite: 60].
* **Descripción:** Como Repartidor, quiero capturar la evidencia digital de recepción (firma/fotografía), para desbloquear el cambio de estado final a "Entregado" y mitigar riesgos legales[cite: 60].

**Criterio de Aceptación 1 (Bloqueo por falta de evidencia):**
* **Dado** que un paquete está "En reparto",[cite: 60]
* **Cuando** el repartidor intenta finalizar la entrega sin adjuntar la firma digital o foto de recepción,[cite: 60]
* **Entonces** la terminal bloquea la transacción y muestra un mensaje de error indicando que la evidencia es obligatoria[cite: 60].

**Criterio de Aceptación 2 (Cierre exitoso vinculado):**
* **Dado** que el repartidor captura la firma/foto digital del receptor,[cite: 60]
* **Cuando** confirma la transacción en la aplicación móvil,[cite: 60]
* **Entonces** el sistema guarda la evidencia vinculada en tiempo real a la guía y cambia el estado a "Entregado"[cite: 60].

---

### Historia 8: Excepción por "Dirección incorrecta"
* **Requerimiento asignado:** BR013, BR003[cite: 61]
* **Necesidad:** Pausa de entrega y notificación a soporte[cite: 61].
* **Descripción:** Como Repartidor, quiero registrar la excepción "Dirección incorrecta" en mi terminal, para pausar el intento de entrega y notificar la incidencia al equipo de atención al cliente[cite: 61].

**Criterio de Aceptación 1 (Pausa de ruta y envío a atención al cliente):**
* **Dado** que el repartidor no localiza la calle o número de destino de un paquete "En reparto",[cite: 61]
* **Cuando** selecciona la opción "Dirección incorrecta" en la aplicación móvil,[cite: 61]
* **Entonces** el sistema pausa la entrega del paquete, registra la incidencia y envía un ticket de corrección a la bandeja de Atención al cliente[cite: 61].

---

### Historia 9: Gestión de "Destinatario ausente" (Segundo intento automático)
* **Requerimiento asignado:** BR014[cite: 61] 
* **Restricción:** Solo se permite un 2° intento automático; el 3° requiere autorización[cite: 61].
* **Descripción:** Como Repartidor, quiero registrar la ausencia del destinatario en la visita, para que el sistema programe automáticamente un segundo intento de entrega[cite: 61].

**Criterio de Aceptación 1 (Programación automática de 2° intento):**
* **Dado** que el repartidor acude al domicilio por primer intento y no encuentra al destinatario,[cite: 61]
* **Cuando** marca la excepción "Destinatario ausente",[cite: 61]
* **Entonces** el sistema cambia el estado a "Segundo intento pendiente" y reagenda de forma automática la entrega para la siguiente jornada[cite: 61].

**Criterio de Aceptación 2 (Restricción de 3er intento):**
* **Dado** que un paquete ya cuenta con dos intentos fallidos por "Destinatario ausente",[cite: 61]
* **Cuando** el repartidor intenta marcar por tercera vez la misma excepción,[cite: 61]
* **Entonces** el sistema bloquea la reprogramación automática y requiere la autorización explícita de un supervisor o Atención al cliente[cite: 61].

---

### Historia 10: Escalamiento de incidencias mayores (Daño o Pérdida)
* **Requerimiento asignado:** BR003[cite: 62]
* **Restricción:** El repartidor no puede resolver incidencias mayores[cite: 62].
* **Descripción:** Como Repartidor, quiero reportar un paquete dañado o con sospecha de pérdida desde la terminal, para escalar el caso inmediatamente a Atención al cliente sin intentar resolverlo en campo[cite: 62].

**Criterio de Aceptación 1 (Escalamiento a atención al cliente):**
* **Dado** que el repartidor detecta que un paquete en ruta presenta un daño estructural grave,[cite: 62]
* **Cuando** selecciona la opción "Reportar daño/incidencia mayor",[cite: 62]
* **Entonces** la terminal impide la entrega al cliente y transfiere automáticamente el control del caso al área de Atención al Cliente para su evaluación[cite: 62].

---

### Historia 11: Generación de alertas por rastreos sin actualización
* **Requerimiento asignado:** BR002[cite: 62]
* **Alcance:** Módulo de alertas automatizadas por inactividad[cite: 62].
* **Descripción:** Como Supervisor de Operaciones, quiero que el sistema genere alertas automáticas ante paquetes sin movimientos por un tiempo prolongado, para evitar la pérdida de visibilidad y detectar estancamientos[cite: 62].

**Criterio de Aceptación 1 (Detención de inactividad):**
* **Dado** que un paquete no ha registrado cambios de estado o escaneos en un periodo mayor al umbral parametrizado (ej. 24/48 horas),[cite: 62]
* **Cuando** se ejecuta el monitoreo automático del sistema,[cite: 62]
* **Entonces** el sistema genera una alerta en la consola del supervisor indicando la guía, el último estado conocido y las horas de estancamiento[cite: 62].

---

### Historia 12: Módulo de consulta de rastreo completo para Atención al Cliente
* **Requerimiento asignado:** BR001, BR004[cite: 62]
* **Criterio de Éxito:** Reducción de llamadas por dudas de rastreo[cite: 62].
* **Descripción:** Como Agente de Atención al Cliente, quiero visualizar el historial completo de eventos y evidencias de una guía en un solo panel, para resolver rápidamente las llamadas de los usuarios sobre sus paquetes[cite: 62].

**Criterio de Aceptación 1 (Centralización de información):**
* **Dado** que un cliente contacta al centro de atención telefónica,[cite: 62]
* **Cuando** el agente ingresa el número de guía única en el sistema,[cite: 62]
* **Entonces** la pantalla muestra la línea de tiempo completa de estados (Recibido, Clasificado, En tránsito, Centro destino, En reparto), la firma/foto digitalizada y el desglose de incidencias ocurridas[cite: 63].

---

### Historia 13: Gestión de rechazo de paquete por el destinatario
* **Requerimiento asignado:** Alcance (Módulo de excepciones operativas)[cite: 63]
* **Descripción:** Como Repartidor, quiero registrar la opción "Paquete rechazado" cuando el cliente no desea recibir el envío, para iniciar el flujo logístico de devolución a la sucursal de origen[cite: 63].

**Criterio de Aceptación 1 (Proceso de retorno):**
* **Dado** que el repartidor se presenta en el domicilio, pero el destinatario indica que rechaza el paquete,[cite: 63]
* **Cuando** el repartidor captura la firma/motivo de rechazo en la terminal,[cite: 63]
* **Entonces** el sistema actualiza el estado a "Rechazado - En proceso de devolución" y reencamina la guía hacia la sucursal de origen[cite: 63].

---

### Historia 14: Centralización y consulta digital de evidencias de entrega
* **Requerimiento asignado:** BR004[cite: 63]
* **Criterio de Éxito:** Centralización del 100% de evidencias digitales[cite: 63].
* **Descripción:** Como Auditor de Calidad / Abogado Interno, quiero consultar las evidencias de recepción vinculadas en tiempo real a las guías, para respaldar legalmente las entregas concretadas y eliminar documentos físicos dispersos[cite: 63].

**Criterio de Aceptación 1 (Acceso a evidencia vinculada):**
* **Dado** que una guía se encuentra en estado "Entregado",[cite: 63]
* **Cuando** el auditor busca el registro en el repositorio central de entregas,[cite: 63]
* **Entonces** el sistema despliega el documento digital con la firma del receptor, fotografía de entrega y timestamp sin desfases de sincronización[cite: 63].

---

### Historia 15: Selección de nivel de servicio al cotizar el envío
* **Requerimiento asignado:** BR005[cite: 63]
* **Alcance:** Nivel de servicio en la tarifa[cite: 63].
* **Descripción:** Como Remitente, quiero elegir entre distintos niveles de servicio (ej. Estándar, Exprés) al cotizar mi envío en sucursal, para ajustar el costo y el tiempo de entrega a mis necesidades[cite: 63].

**Criterio de Aceptación 1 (Ajuste por nivel de servicio):**
* **Dado** que el cliente solicita cotizar un paquete con peso y dimensiones fijas,[cite: 64]
* **Cuando** el empleado cambia el parámetro de "Servicio Estándar" a "Servicio Exprés",[cite: 64]
* **Entonces** el sistema vuelve a calcular la tarifa automáticamente aplicando las reglas del tabulador y ajusta la promesa de entrega correspondiente en el comprobante[cite: 64].


## 4. Trazabilidad entre Artefactos
Esta sección demuestra la coherencia obligatoria entre los requerimientos (User Stories), las reglas del negocio, los actores, el código de dominio implementado y las decisiones arquitectónicas (ADRs).

* **US-01 y US-15 (Cotización de envío)**
  * **Regla:** BR005 (Cálculo estricto por sistema; sin modificación manual).
  * **Implementación:** `CalculadoraTarifa`, `Paquete`.
  * **Arquitectura:** ADR-01 (Domain Model para encapsular lógica matemática).

* **US-02 (Generar Guía única)**
  * **Regla:** BR006 (Generación de guía asignando estado inicial 'Recibido').
  * **Implementación:** `Paquete.CrearGuia()`, `GuiaValueObject`.
  * **Arquitectura:** ADR-01 (Garantiza invariantes al crear la entidad).

* **US-03 y US-04 (Rastreo e Instalaciones)**
  * **Regla:** BR008 (Escaneo obligatorio) y BR002 (Trazabilidad ininterrumpida).
  * **Implementación:** `Paquete.MarcarEnTransito()`, `EventosRastreo`.
  * **Arquitectura:** ADR-02 (Límites de agregados y consistencia de eventos).

* **US-07 y US-13 (Cierre y Excepciones logísticas)**
  * **Regla:** BR012 y BR004 (Estado 'Entregado' bloqueado sin evidencia. El rechazo reencamina).
  * **Implementación:** `Paquete.FinalizarEntrega(Evidencia)`, `Paquete.RegistrarRechazo()`.
  * **Arquitectura:** ADR-01 y ADR-03 (Service Layer delgada).

* **US-09 (Límite de Intentos Fallidos)**
  * **Regla:** BR014 (Límite de 2 intentos automáticos; el 3er intento requiere autorización).
  * **Implementación:** `Paquete.RegistrarIntentoFallido()`, `TercerIntentoNoAutorizadoException`.
  * **Arquitectura:** ADR-01 (Domain Model con excepciones de negocio).

* **US-12 (Módulo de Consulta)**
  * **Regla:** BR001 (Consulta en tiempo real sin bloquear escrituras).
  * **Implementación:** `ObtenerRastreoPorGuiaQuery`, `RastreoPaqueteDTO`.
  * **Arquitectura:** ADR-03 (Separación de consultas CQRS básico).