from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum


class TipoServicio(str, Enum):
    inalambrico = "inalambrico"
    fibra = "fibra"
    tv = "tv"


class PlanBase(SQLModel):
    nombre: str = Field(index=True)
    velocidad_subida: int  # Mbps
    velocidad_bajada: int  # Mbps
    precio: float
    tipo: TipoServicio = TipoServicio.inalambrico
    descripcion: Optional[str] = None
    activo: bool = True


class Plan(PlanBase, table=True):
    __tablename__ = "planes"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PlanCreate(PlanBase):
    pass


class PlanUpdate(SQLModel):
    nombre: Optional[str] = None
    velocidad_subida: Optional[int] = None
    velocidad_bajada: Optional[int] = None
    precio: Optional[float] = None
    tipo: Optional[TipoServicio] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class PlanRead(PlanBase):
    id: int
    created_at: datetime
