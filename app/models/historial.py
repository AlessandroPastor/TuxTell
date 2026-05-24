from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum


class TipoEvento(str, Enum):
    instalacion = "instalacion"
    cambio_plan = "cambio_plan"
    corte = "corte"
    reconexion = "reconexion"
    cambio_equipo = "cambio_equipo"
    observacion = "observacion"
    baja = "baja"


class Historial(SQLModel, table=True):
    __tablename__ = "historial"
    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="clientes.id", index=True)
    tipo: TipoEvento
    descripcion: str
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HistorialRead(SQLModel):
    id: int
    cliente_id: int
    tipo: TipoEvento
    descripcion: str
    usuario_id: Optional[int]
    created_at: datetime
