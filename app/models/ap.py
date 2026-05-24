from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum


class FrecuenciaAP(str, Enum):
    ghz_2_4 = "2.4GHz"
    ghz_5 = "5GHz"
    dual = "dual"


class APBase(SQLModel):
    nombre: str = Field(index=True)        # "AP-Sector-Norte", "AP-Cabanillas-01"
    base_id: int = Field(foreign_key="bases.id")
    marca: Optional[str] = None
    modelo: Optional[str] = None
    frecuencia: Optional[FrecuenciaAP] = None
    mac_address: Optional[str] = None
    # IP de gestión del AP (no del túnel, sino la IP local del AP)
    ip_gestion: Optional[str] = None
    usuario_acceso: Optional[str] = None
    clave_acceso: Optional[str] = None


class AP(APBase, table=True):
    __tablename__ = "access_points"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class APCreate(APBase):
    pass


class APUpdate(SQLModel):
    nombre: Optional[str] = None
    base_id: Optional[int] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    frecuencia: Optional[FrecuenciaAP] = None
    mac_address: Optional[str] = None
    ip_gestion: Optional[str] = None
    usuario_acceso: Optional[str] = None
    clave_acceso: Optional[str] = None


class APRead(SQLModel):
    id: int
    nombre: str
    base_id: int
    marca: Optional[str]
    modelo: Optional[str]
    frecuencia: Optional[FrecuenciaAP]
    mac_address: Optional[str]
    ip_gestion: Optional[str]
    # clave_acceso NO se expone
