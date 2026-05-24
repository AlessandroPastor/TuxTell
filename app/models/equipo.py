from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum


class TipoEquipo(str, Enum):
    router = "router"
    cpe = "cpe"      # antena cliente


class EstadoEquipo(str, Enum):
    activo = "activo"
    devuelto = "devuelto"
    danado = "dañado"
    perdido = "perdido"


class EquipoBase(SQLModel):
    cliente_id: int = Field(foreign_key="clientes.id", index=True)
    tipo: TipoEquipo
    marca: Optional[str] = None
    modelo: Optional[str] = None
    mac_address: Optional[str] = None
    numero_serie: Optional[str] = None
    es_prestado: bool = False
    estado: EstadoEquipo = EstadoEquipo.activo


class Equipo(EquipoBase, table=True):
    __tablename__ = "equipos"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EquipoCreate(EquipoBase):
    pass


class EquipoUpdate(SQLModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    mac_address: Optional[str] = None
    numero_serie: Optional[str] = None
    es_prestado: Optional[bool] = None
    estado: Optional[EstadoEquipo] = None


class EquipoRead(EquipoBase):
    id: int
    created_at: datetime
