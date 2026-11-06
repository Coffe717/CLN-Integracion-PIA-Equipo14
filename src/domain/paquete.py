from datetime import datetime

class Paquete:
    def __init__(self, id_paquete: str, destino: str):
        self.id_paquete = id_paquete
        self.destino = destino
        self.estado = "Recibido"  # Estado inicial
        self.evidencia_firmada = False

    def clasificar(self):
        if self.estado != "Recibido":
            raise ValueError("El paquete solo puede ser clasificado desde el estado 'Recibido'.")
        self.estado = "Clasificado"

    def poner_en_transito(self):
        if self.estado != "Clasificado":
            raise ValueError("El paquete debe estar clasificado antes de ponerse en tránsito.")
        self.estado = "En Tránsito"

    def entregar(self, evidencia: bool):
        if self.estado != "En Tránsito":
            raise ValueError("El paquete debe estar en tránsito para poder entregarse.")
        
        # Regla de negocio: Bloquear la entrega si no hay evidencia
        if not evidencia:
            raise ValueError("No se puede entregar el paquete: falta la evidencia de firma o entrega.")
        
        self.evidencia_firmada = True
        self.estado = "Entregado"