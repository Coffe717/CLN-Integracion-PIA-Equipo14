# Matriz de trazabilidad: BRD → historia → regla → componente → prueba
Pruebas en `tests/`. Los casos **CP-xx** son los de la tabla del PIA; se prueban en el dominio (`tests/unit/test_casos_pia_imagen.py`) y de extremo a extremo (`tests/integration/test_casos_pia_extremo_a_extremo.py`).

| BR | Historia | Regla de negocio | Componente (código) | Prueba |
|----|----------|------------------|---------------------|--------|
| BR005 | HU-01, HU-15 | Tarifa estricta por sistema, sin edición | `tabulador.py` · `Tarifa` (inmutable) | **CP-07**, **CP-08** · `test_valores_y_tarifa.py` · `test_api::test_cotizacion_cp07_y_validaciones` |
| BR006 | HU-02 | Guía única | `GuiaRastreo` · `GeneradorGuiaUuid` | `test_servicios::test_recepcion_genera_guia…` · `test_generador_guia_unica` |
| BR007 | HU-02 | Estado inicial Recibido | `Paquete.recibir` | `test_dominio::test_recibir_genera_guia…` |
| BR008 | HU-03 | Clasificado solo desde Recibido | `Paquete.clasificar` · `MaquinaEstados` | `test_dominio::TestMaquinaEstados` · `test_no_se_puede_clasificar_dos_veces` |
| BR009 | HU-04 | En tránsito vía manifiesto (atómico) | `ManifiestoViaje` · `OperacionLogisticaService` | `test_servicios::test_manifiesto_es_atomico` · `test_manifiesto_y_arribo…` |
| BR010 | HU-05 | Centro destino solo desde En tránsito | `Paquete.marcar_centro_destino` | `test_servicios::test_manifiesto_y_arribo…` · `test_api::test_rechazo_devolucion_y_manifiesto_arribo` |
| BR011 | HU-06 | En reparto al iniciar ruta | `RutaReparto` · `EntregaService.iniciar_ruta_reparto` | `test_servicios::test_flujo_completo…` · `test_dominio::TestManifiestoYRuta` |
| BR012 | HU-07 | Sin evidencia no hay Entregado | `Paquete.finalizar_entrega` · `EvidenciaObligatoriaException` | **CP-01, CP-02, CP-03** · `test_api::test_cp01/02/03…` |
| BR004 | HU-07, HU-14 | Evidencia ligada a la guía | `EvidenciaRecepcion` · `consultar_evidencia_entrega` | `test_servicios::test_evidencia_solo_si_hay_entrega` · `test_repositorios_sql::test_evidencia_se_persiste` |
| BR013 | HU-08 | Dirección incorrecta pausa y abre ticket | `pausar_por_direccion_incorrecta` · `Incidencia` | `test_servicios::test_direccion_incorrecta_ticket_y_correccion` |
| BR014 | HU-09 | 2.º intento automático; 3.º autorizado | `registrar_ausencia` · `AutorizacionReintento` | **CP-04, CP-05, CP-06** · `test_api::test_cp04_cp05_cp06_intentos_api` |
| BR003 | HU-10 | Repartidor no resuelve incidencias mayores | `Incidencia.resolver` · `ResolucionNoPermitidaException` | `test_dominio::TestIncidencia` · `test_servicios::test_incidencia_mayor_se_escala` |
| BR002 | HU-11 | Alerta por inactividad | `PaqueteEstancadoSpec` · `MonitoreoService` | `test_servicios::test_monitoreo_estancados` · `TestEspecificaciones::test_estancado` |
| BR001 | HU-12 | Rastreo completo para atención | `ConsultaRastreoService` | `test_api::test_rastreo_y_404` |
| Alcance | HU-13 | Rechazo → logística inversa | `registrar_rechazo` · `completar_devolucion` | `test_dominio::test_rechazo_inicia_logistica_inversa` |

**Specifications:** `PaqueteEstancadoSpec`, `RequiereAutorizacionTercerIntentoSpec`, `PuedeEnviarSpec` (+ `EstadoEnSpec`, `EsTerminalSpec`…) combinadas con `&`, `|`, `~` → `test_dominio::TestEspecificaciones`.
**Domain Events:** 24 eventos en `domain/eventos.py`; los manejadores crean avisos en `application/eventos.py`.
