from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime, date
from enum import Enum


class MetodoPago(str, Enum):
    yape = "yape"
    transferencia = "transferencia"
    efectivo = "efectivo"
    plin = "plin"


class PagoBase(SQLModel):
    cliente_id: int = Field(foreign_key="clientes.id", index=True)
    monto: float
    fecha_pago: datetime = Field(default_factory=datetime.utcnow)
    # mes_correspondiente: primer día del mes que cubre el pago
    # ej: date(2026, 5, 1) = pago de mayo 2026
    mes_correspondiente: date
    metodo: MetodoPago
    comprobante_url: Optional[str] = None
    observacion: Optional[str] = None
    registrado_por_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")


class Pago(PagoBase, table=True):
    __tablename__ = "pagos"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PagoCreate(SQLModel):
    cliente_id: int
    monto: float
    fecha_pago: Optional[datetime] = None
    mes_correspondiente: date
    metodo: MetodoPago
    observacion: Optional[str] = None
    # comprobante_url se asigna tras subir el archivo


class PagoRead(PagoBase):
    id: int
    created_at: datetime
