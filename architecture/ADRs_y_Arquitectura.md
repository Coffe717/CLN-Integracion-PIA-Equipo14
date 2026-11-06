# Arquitectura y Decisiones Técnicas - CargoBox

## 1. Patrones de Diseño Aplicados y SOLID
* **Domain Model:** Se encapsuló la lógica compleja en entidades como `Paquete` para asegurar que las reglas (como evidencia obligatoria o límites de intentos) se validen en memoria.
* **Repository Pattern & CQRS Básico:** Se separaron las escrituras (Commands) de las lecturas masivas (Queries) mediante DTOs para no sobrecargar el Agregado.
* **Dependency Inversion Principle (DIP):** Los Application Services solo dependen de interfaces (`IPaqueteRepository`), aislando completamente la base de datos e infraestructura.

## 2. Architecture Decision Records (ADRs)

### ADR-001: Adoptar Domain Model como patrón de lógica de negocio
* **Contexto:** CargoBox no es un CRUD: es un flujo logístico con una máquina de estados e invariantes (evidencia obligatoria, tarifa calculada por el sistema).
* **Decisión:** Usar Domain Model, con `Paquete` como Aggregate Root que expone métodos con intención (`marcarEnTransito`, `finalizarEntrega`) y lanza excepciones de dominio. Las reglas se validan en memoria antes de tocar la base de datos.
* **Consecuencias:** Reglas centralizadas, pruebas unitarias sin base de datos y lenguaje ubicuo en el código. Aumenta la curva de aprendizaje inicial.

### ADR-002: Límites de los agregados y consistencia entre ellos
* **Contexto:** Paquete debe mantener consistentes su estado, su historial y sus intentos. Un manifiesto afecta a muchos paquetes a la vez, y las incidencias las gestiona Atención al cliente con su propio ciclo de vida.
* **Decisión:** `EventoRastreo` vive dentro de `Paquete`. `Incidencia`, `ManifiestoViaje` y `RutaReparto` son agregados propios que guardan `GuiaRastreo` como referencia. Cada transacción modifica un solo agregado.
* **Consecuencias:** Beneficios: invariantes protegidas, transacciones cortas, menos bloqueos de base de datos. Costos: consistencia eventual (un paquete puede tardar milisegundos en reflejar «En tránsito»).

### ADR-003: Service Layer delgada y Repository como puertos
* **Contexto:** Los casos de uso los invocan actores distintos. Se necesita probar las reglas sin base de datos y evitar que la Service Layer se llene de lógica.
* **Decisión:** Cada método de servicio representa un caso de uso. Las interfaces (`IPaqueteRepository`) se implementan en infraestructura. Las reglas viven puramente en el dominio.
* **Consecuencias:** El dominio puede ser probado con dobles (mocks), y la base de datos se puede cambiar sin tocar las reglas.