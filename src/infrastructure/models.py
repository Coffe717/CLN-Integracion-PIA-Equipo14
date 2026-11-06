from sqlalchemy import Column, String, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class PaqueteModel(Base):
    __tablename__ = "paquetes"

    id_paquete = Column(String, primary_key=True)
    destino = Column(String, nullable=False)
    estado = Column(String, nullable=False)
    evidencia_firmada = Column(Boolean, default=False)

def get_db_engine():
    # Base de datos SQLite local
    engine = create_engine("sqlite:///paquetes.db", echo=False)
    Base.metadata.create_all(engine)
    return engine