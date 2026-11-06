from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.domain.paquete import Paquete
from src.infrastructure.models import PaqueteModel, get_db_engine, sessionmaker

app = FastAPI(
    title="API de Gestión de Paquetes - CargoBox",
    description="API REST para el control de paquetes, máquina de estados y reglas de negocio.",
    version="1.0.0"
)

engine = get_db_engine()
SessionLocal = sessionmaker(bind=engine)

class PaqueteCreate(BaseModel):
    id_paquete: str
    destino: str

class EvidenciaRequest(BaseModel):
    evidencia: bool

@app.post("/paquetes/", response_model=dict)
def crear_paquete(datos: PaqueteCreate):
    db: Session = SessionLocal()
    existente = db.query(PaqueteModel).filter(PaqueteModel.id_paquete == datos.id_paquete).first()
    if existente:
        db.close()
        raise HTTPException(status_code=400, detail="El paquete ya existe.")
    
    nuevo_paquete = PaqueteModel(
        id_paquete=datos.id_paquete,
        destino=datos.destino,
        estado="Recibido",
        evidencia_firmada=False
    )
    db.add(nuevo_paquete)
    db.commit()
    db.close()
    return {"mensaje": "Paquete creado con éxito", "id_paquete": datos.id_paquete, "estado": "Recibido"}

@app.put("/paquetes/{id_paquete}/clasificar")
def clasificar_paquete(id_paquete: str):
    db: Session = SessionLocal()
    db_paq = db.query(PaqueteModel).filter(PaqueteModel.id_paquete == id_paquete).first()
    if not db_paq:
        db.close()
        raise HTTPException(status_code=404, detail="Paquete no encontrado.")
    
    # Instanciamos la lógica de dominio
    paq = Paquete(db_paq.id_paquete, db_paq.destino)
    paq.estado = db_paq.estado
    
    try:
        paq.clasificar()
        db_paq.estado = paq.estado
        db.commit()
    except ValueError as e:
        db.close()
        raise HTTPException(status_code=400, detail=str(e))
    
    db.close()
    return {"mensaje": "Paquete clasificado correctamente", "estado": paq.estado}

@app.put("/paquetes/{id_paquete}/transito")
def poner_en_transito(id_paquete: str):
    db: Session = SessionLocal()
    db_paq = db.query(PaqueteModel).filter(PaqueteModel.id_paquete == id_paquete).first()
    if not db_paq:
        db.close()
        raise HTTPException(status_code=404, detail="Paquete no encontrado.")
    
    paq = Paquete(db_paq.id_paquete, db_paq.destino)
    paq.estado = db_paq.estado
    
    try:
        paq.poner_en_transito()
        db_paq.estado = paq.estado
        db.commit()
    except ValueError as e:
        db.close()
        raise HTTPException(status_code=400, detail=str(e))
    
    db.close()
    return {"mensaje": "Paquete puesto en tránsito", "estado": paq.estado}

@app.put("/paquetes/{id_paquete}/entregar")
def entregar_paquete(id_paquete: str, body: EvidenciaRequest):
    db: Session = SessionLocal()
    db_paq = db.query(PaqueteModel).filter(PaqueteModel.id_paquete == id_paquete).first()
    if not db_paq:
        db.close()
        raise HTTPException(status_code=404, detail="Paquete no encontrado.")
    
    paq = Paquete(db_paq.id_paquete, db_paq.destino)
    paq.estado = db_paq.estado
    
    try:
        paq.entregar(body.evidencia)
        db_paq.estado = paq.estado
        db_paq.evidencia_firmada = paq.evidencia_firmada
        db.commit()
    except ValueError as e:
        db.close()
        raise HTTPException(status_code=400, detail=str(e))
    
    db.close()
    return {"mensaje": "Paquete entregado con éxito", "estado": paq.estado, "evidencia_firmada": paq.evidencia_firmada}