"""
Router de Bases (Routers MikroTik físicos).
Las IPs se configuran aquí — sin tocar código ni .env.
"""
from typing import Annotated, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models.base import BaseRed, BaseRedCreate, BaseRedUpdate, BaseRedRead, BaseRedReadAdmin
from app.models.usuario import RolUsuario
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario
from app.services import mikrotik_service

router = APIRouter(prefix="/bases", tags=["bases"])


def _require_admin(usuario: Usuario):
    if usuario.rol != RolUsuario.admin:
        raise HTTPException(status_code=403, detail="Solo admin puede realizar esta acción")


@router.get("/", response_model=List[BaseRedRead])
def listar_bases(session: Annotated[Session, Depends(get_session)]):
    return session.exec(select(BaseRed)).all()


@router.post("/", response_model=BaseRedRead)
def crear_base(
    data: BaseRedCreate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    _require_admin(usuario)
    base = BaseRed(**data.model_dump())
    session.add(base)
    session.commit()
    session.refresh(base)
    return base


@router.get("/{base_id}", response_model=BaseRedReadAdmin)
def obtener_base(
    base_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    _require_admin(usuario)
    base = session.get(BaseRed, base_id)
    if not base:
        raise HTTPException(status_code=404, detail="Base no encontrada")
    return base


@router.put("/{base_id}", response_model=BaseRedRead)
def actualizar_base(
    base_id: int,
    data: BaseRedUpdate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    """
    Actualiza los datos de una base. Usa este endpoint para configurar
    ip_vpn, usuario_api y clave_api cuando el túnel L2TP esté activo.
    """
    _require_admin(usuario)
    base = session.get(BaseRed, base_id)
    if not base:
        raise HTTPException(status_code=404, detail="Base no encontrada")

    cambios = data.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(base, campo, valor)
    base.updated_at = datetime.utcnow()
    session.add(base)
    session.commit()
    session.refresh(base)
    return base


@router.get("/{base_id}/estado")
def verificar_estado(
    base_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """Verifica si el MikroTik de la base responde por RouterOS API."""
    base = session.get(BaseRed, base_id)
    if not base:
        raise HTTPException(status_code=404, detail="Base no encontrada")

    if not base.ip_vpn:
        return {
            "base": base.nombre,
            "estado": "no_configurado",
            "mensaje": "La base no tiene ip_vpn configurada. Usa PUT /bases/{id} para configurarla.",
        }

    try:
        estado = mikrotik_service.verificar_estado_base(session, base_id)
        return {"base": base.nombre, "estado": estado}
    except mikrotik_service.MikrotikNoConfigurado as e:
        return {"base": base.nombre, "estado": "no_configurado", "mensaje": str(e)}
    except mikrotik_service.MikrotikOffline as e:
        return {"base": base.nombre, "estado": "offline", "mensaje": str(e)}
