from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum


class RolUsuario(str, Enum):
    admin = "admin"
    tecnico = "tecnico"
    cobrador = "cobrador"


class UsuarioBase(SQLModel):
    nombre: str
    email: str = Field(unique=True, index=True)
    rol: RolUsuario = RolUsuario.tecnico
    activo: bool = True


class Usuario(UsuarioBase, table=True):
    __tablename__ = "usuarios"
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioUpdate(SQLModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None
    password: Optional[str] = None


class UsuarioRead(UsuarioBase):
    id: int
    created_at: datetime
