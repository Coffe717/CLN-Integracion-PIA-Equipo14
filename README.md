# 📦 CargoBox · Gestión y rastreo de envíos
PIA · Componentes de Lógica de Negocios · UANL-FIME · Equipo 14 (Grupo 002)

Aplicación web para registrar paquetes, seguirlos en tiempo real y cerrar la entrega con evidencia.
Implementa **DDD + Specification + State Machine + API REST (OpenAPI)** a partir del BRD, historias de usuario, BPMN y glosario del equipo.

- **Repositorio:** https://github.com/Coffe717/CLN-Integracion-PIA-Equipo14
- **Sistema desplegado:** https://cln-integracion-pia-equipo14.onrender.com  ·  Swagger: https://cln-integracion-pia-equipo14.onrender.com/docs

## Qué puede hacer cada persona (pestañas de la interfaz)
| Pestaña | Para qué |
|---|---|
| 🔎 Rastrear mi paquete | El cliente escribe su guía y ve el estado, el recorrido y mensajes sencillos |
| 🏪 Sucursal | Cotiza (precio automático), confirma recepción y genera la guía; cancela o confirma devoluciones |
| 🏭 Centro de distribución | Clasifica, despacha viajes (manifiesto) y registra llegadas |
| 🚚 Repartidor | Inicia ruta; entrega con firma/foto; marca ausente, rechazo, dirección incorrecta, daño/pérdida |
| 🎧 Atención al cliente | Resuelve tickets y autoriza el 3.er intento |
| 📊 Supervisor | Detecta paquetes estancados y autoriza reintentos |
| 🧾 Auditoría | Consulta firma, foto y hora de cada entrega |

La pantalla se actualiza sola cada 6 segundos.

## Ejecutar
### Opción 1 · Local (SQLite, sin Docker)
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                   # opcional
python wsgi.py                                         # http://localhost:8000
```
### Opción 2 · Docker Compose (PostgreSQL + App + Tests)
```bash
cp .env.example .env
docker compose up --build            # App: http://localhost:8000  ·  Swagger: /docs
docker compose run --rm tests        # pruebas contra el entorno de Compose
```
### Despliegue
`render.yaml` define el servicio web (Docker) y la base PostgreSQL. En Render: *New + → Blueprint* y elige el repo. Swagger queda activo en `/docs`.

## Pruebas
```bash
pytest                      # incluye cobertura y falla si es < 80 % (ver pytest.ini)
pytest -m cp -v             # solo los casos CP-01 … CP-08 (también supera el 80 % por sí sola)
pytest tests/unit           # solo unitarias
pytest tests/integration    # solo integración
```
Cobertura medida: suite completa ≈99.9 % · solo casos CP ≈82 % · solo unitarias ≈89 % · solo integración ≈96 %.
`pytest.ini` exige `--cov-fail-under=80`: cualquiera de estos comandos falla si baja de 80 %.
| Carpeta | Contenido |
|---|---|
| `tests/unit/test_casos_pia_imagen.py` | **CP-01 a CP-08** (evidencia BR012, intentos BR014, tarifa BR005) |
| `tests/unit/` | Value Objects, tarifa, máquina de estados, Specifications, agregados, casos de uso |
| `tests/integration/test_casos_pia_extremo_a_extremo.py` | **CP-01 a CP-08** de extremo a extremo: API → servicios → dominio → BD (memoria y SQLite) |
| `tests/integration/` | Repositorios SQL, API REST completa (200/201/400/403/404/409/422), semilla y OpenAPI |

## Estructura
```
docs/        BRD.md · historias_usuario.md · gherkin/ · glosario.md · trazabilidad.md
             architecture/ (ADRs, decisiones, diagramas .drawio) · api/openapi.json · analisis/ (PDF originales)
src/domain/          entidades, Value Objects, agregados, eventos, State Machine, Specifications
src/application/     servicios (casos de uso), puertos, eventos, DTO
src/infrastructure/  repositorios SQL y memoria, Unit of Work, mappers, composición, semilla
src/api/             Flask: rutas REST, OpenAPI, interfaz web (static/)
tests/  .github/workflows/ci.yml  docker-compose.yml  Dockerfile  .env.example  render.yaml
```

## API
Contrato: **200/201** éxito · **400** solicitud mal formada · **403** rol no permitido · **404** no existe · **409** conflicto (transición inválida, 3.er intento) · **422** validación (evidencia obligatoria, peso negativo).
Documentación interactiva en `/docs`; especificación en `/openapi.json` y `docs/api/openapi.json`.

## Demo sugerida (5 min)
1. **Sucursal**: cotizar 5 kg 30×30×30 Estándar en Monterrey → **$150.00 MXN** (CP-07) → confirmar y copiar la guía.
2. **Centro**: clasificar → despachar viaje → registrar llegada.
3. **Repartidor**: iniciar ruta → intentar *Entregar* sin firma (bloqueado, CP-02) → entregar con firma (CP-01).
4. **Repartidor**: *No estaba* dos veces → *No estaba* otra vez (bloqueado, CP-05) → **Atención** autoriza → *No estaba* (Retenido en sucursal, CP-06).
5. **Rastreo** y **Auditoría**: recorrido completo y evidencia. **Supervisor**: alertas de estancados.

Trazabilidad BRD → regla → componente → prueba: `docs/trazabilidad.md`.
