import pytest

from src.domain.incidencia import Incidencia
from src.domain.manifiesto import ManifiestoViaje, RutaReparto
from src.domain.valores import Instalacion
from src.infrastructure.db import Database
from src.infrastructure.composicion import construir_sql
from src.infrastructure.repositorios_sql import GeneradorGuiaUuid, SqlUnitOfWork
from src.infrastructure.mappers import paquete_a_dict, paquete_desde_dict
from tests.helpers import autorizacion, con_dos_ausencias, evidencia, paquete_en
from src.domain.estado import EstadoEnvio as E


def test_paquete_ida_y_vuelta_conserva_todo(sql):
    repo = sql.logistica._paquetes
    p = con_dos_ausencias(paquete_en(E.EN_REPARTO))
    p.autorizar_tercer_intento(autorizacion())
    repo.guardar(p)
    x = repo.obtener_por_guia(str(p.guia))
    assert x.estado is p.estado and x.intentos_fallidos == 2 and x.autorizacion.rol == "SUPERVISOR"
    assert len(x.historial) == len(p.historial) and x.tarifa.total == p.tarifa.total
    assert repo.obtener_por_guia("CB-0000000000") is None


def test_evidencia_se_persiste(sql):
    repo = sql.logistica._paquetes
    p = paquete_en(E.ENTREGADO)
    repo.guardar(p)
    assert repo.obtener_por_guia(str(p.guia)).evidencia.firma == evidencia().firma
    assert paquete_desde_dict(paquete_a_dict(p)).estado is E.ENTREGADO


def test_guardar_dos_veces_actualiza(sql):
    repo = sql.logistica._paquetes
    p = paquete_en(E.CLASIFICADO)
    repo.guardar(p)
    p.marcar_en_transito("M")
    repo.guardar(p)
    assert len(repo.listar()) == 1 and repo.listar(estado="EN_TRANSITO")[0].estado is E.EN_TRANSITO


def test_incidencia_manifiesto_ruta(sql):
    inc = Incidencia.abrir("CB-0000000001", "DANO", "roto", "Juan")
    sql.incidencias._incidencias.guardar(inc)
    leida = sql.incidencias._incidencias.obtener(inc.id)
    assert leida.tipo.value == "DANO"
    leida.resolver("Laura", "ATENCION_CLIENTE", "ok")
    sql.incidencias._incidencias.guardar(leida)
    assert sql.incidencias.listar_incidencias("RESUELTA")[0]["resuelta_por"] == "Laura"
    m = ManifiestoViaje.crear(Instalacion("A"), Instalacion("B"), ["CB-1"])
    m.despachar()
    repo_m = sql.logistica._manifiestos
    repo_m.guardar(m)
    assert repo_m.obtener(m.id).estado.value == "DESPACHADO" and repo_m.obtener("X") is None
    r = RutaReparto.crear("Juan", ["CB-1"])
    sql.entrega._rutas.guardar(r)
    assert sql.entrega._rutas.obtener(r.id).repartidor == "Juan" and sql.entrega._rutas.obtener("X") is None


def test_unit_of_work_hace_rollback(sql):
    db = sql.db
    uow = SqlUnitOfWork(db)
    with pytest.raises(RuntimeError):
        with uow:
            db.ejecutar("INSERT INTO notificaciones (id,destino,mensaje,guia,creada_en) VALUES ('1','A','m','g','t')")
            raise RuntimeError("falla")
    assert db.consultar("SELECT * FROM notificaciones") == []
    with uow:
        with uow:  # anidado reutiliza la transacción
            db.ejecutar("INSERT INTO notificaciones (id,destino,mensaje,guia,creada_en) VALUES ('2','A','m','g','t')")
    assert len(db.consultar("SELECT * FROM notificaciones")) == 1


def test_base_en_archivo_persiste(tmp_path):
    url = f"sqlite:///{tmp_path}/sub/cargobox.db"
    c1 = construir_sql(url)
    c1.remitentes.guardar(__import__("src.domain.remitente", fromlist=["x"]).Remitente("R9", "Nueve", True, False, "MTY"))
    c2 = construir_sql(url)
    assert c2.remitentes.obtener("R9").nombre == "Nueve"
    assert c2.remitentes.obtener("NADA") is None


def test_url_invalida():
    with pytest.raises(ValueError):
        Database("mysql://x")


def test_generador_guia_unica():
    g = GeneradorGuiaUuid()
    assert len({str(g.generar()) for _ in range(200)}) == 200
