from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum


class EstadoBase(str, Enum):
    online = "online"
    offline = "offline"
    desconocido = "desconocido"


class BaseRedBase(SQLModel):
    nombre: str = Field(index=True)                 # "Cabanillas", "Palca", "Paratia"
    ubicacion: Optional[str] = None                 # coordenadas o descripción
    # ── IPs configurables desde la app ─────────────────────────────
    # Dejar en None hasta tener la infraestructura lista.
    # Cambiar con PUT /bases/{id} cuando el túnel L2TP esté activo.
    ip_vpn: Optional[str] = None                    # ej: "10.10.0.2" (IP WireGuard del router)
    usuario_api: Optional[str] = None               # usuario RouterOS API
    clave_api: Optional[str] = None                 # contraseña RouterOS API (encriptada en app)
    puerto_api: int = 8728                          # puerto RouterOS API
    estado: EstadoBase = EstadoBase.desconocido


class BaseRed(BaseRedBase, table=True):
    __tablename__ = "bases"
    id: Optional[int] = Field(default=None, primary_key=True)
    ultima_verificacion: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BaseRedCreate(SQLModel):
    nombre: str
    ubicacion: Optional[str] = None
    ip_vpn: Optional[str] = None          # se puede crear sin IP y agregarla después
    usuario_api: Optional[str] = None
    clave_api: Optional[str] = None
    puerto_api: int = 8728


class BaseRedUpdate(SQLModel):
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    ip_vpn: Optional[str] = None          # actualizar cuando el túnel esté activo
    usuario_api: Optional[str] = None
    clave_api: Optional[str] = None
    puerto_api: Optional[int] = None


class BaseRedRead(SQLModel):
    id: int
    nombre: str
    ubicacion: Optional[str]
    ip_vpn: Optional[str]
    puerto_api: int
    estado: EstadoBase
    ultima_verificacion: Optional[datetime]
    # clave_api NO se expone en la respuesta


class BaseRedReadAdmin(BaseRedRead):
    usuario_api: Optional[str]  # solo admin ve el usuario
