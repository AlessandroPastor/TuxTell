from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime, date
from enum import Enum


class EstadoCliente(str, Enum):
    activo = "activo"
    cortado = "cortado"       # corte por falta de pago
    suspendido = "suspendido" # suspensión voluntaria o técnica
    baja = "baja"             # ya no es cliente (soft delete)


class TipoServicio(str, Enum):
    inalambrico = "inalambrico"
    fibra = "fibra"
    tv = "tv"


class ClienteBase(SQLModel):
    # ── Datos personales ────────────────────────────────────────────
    nombre: str
    apellido: str
    dni: str = Field(index=True)
    telefono: str                          # WhatsApp
    direccion: str
    coordenadas: Optional[str] = None     # "lat,lng" para navegación del técnico
    foto_url: Optional[str] = None

    # ── Servicio ────────────────────────────────────────────────────
    tipo_servicio: TipoServicio = TipoServicio.inalambrico
    plan_id: int = Field(foreign_key="planes.id")
    base_id: int = Field(foreign_key="bases.id")
    ap_id: Optional[int] = Field(default=None, foreign_key="access_points.id")
    fecha_instalacion: date
    dia_corte: int = Field(ge=1, le=28)   # 1-28 (evita problemas con feb)
    estado: EstadoCliente = EstadoCliente.activo

    # ── Credenciales PPPoE ──────────────────────────────────────────
    usuario_pppoe: Optional[str] = None
    clave_pppoe: Optional[str] = None     # se almacena cifrada


class Cliente(ClienteBase, table=True):
    __tablename__ = "clientes"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    fecha_baja: Optional[datetime] = None  # soft delete


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(SQLModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    coordenadas: Optional[str] = None
    foto_url: Optional[str] = None
    plan_id: Optional[int] = None
    base_id: Optional[int] = None
    ap_id: Optional[int] = None
    dia_corte: Optional[int] = None
    estado: Optional[EstadoCliente] = None
    usuario_pppoe: Optional[str] = None
    clave_pppoe: Optional[str] = None


class ClienteRead(SQLModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    telefono: str
    direccion: str
    coordenadas: Optional[str]
    foto_url: Optional[str]
    tipo_servicio: TipoServicio
    plan_id: int
    base_id: int
    ap_id: Optional[int]
    fecha_instalacion: date
    dia_corte: int
    estado: EstadoCliente
    usuario_pppoe: Optional[str]
    created_at: datetime
    # clave_pppoe NO se expone en listados generales


class ClienteReadDetalle(ClienteRead):
    clave_pppoe: Optional[str]  # solo en vista detalle con permiso
