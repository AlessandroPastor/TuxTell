"""
Control MikroTik en tiempo real.
Si la base no tiene IP configurada, responde con 503 explicativo
en lugar de crashear — así Flutter puede mostrar un mensaje claro.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.base import BaseRed
from app.models.cliente import Cliente, EstadoCliente
from app.models.historial import Historial, TipoEvento
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario
from app.services import mikrotik_service
from app.services.mikrotik_service import MikrotikNoConfigurado, MikrotikOffline, MikrotikError

router = APIRouter(prefix="/mikrotik", tags=["mikrotik"])


def _manejar_error_mikrotik(e: Exception, base_nombre: str):
    if isinstance(e, MikrotikNoConfigurado):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Base '{base_nombre}' sin IP configurada. Configúrala en PUT /bases/{{id}}",
        )
    if isinstance(e, MikrotikOffline):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Base '{base_nombre}' no responde. Verifica el túnel WireGuard.",
        )
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/estado-bases")
def estado_todas_las_bases(session: Annotated[Session, Depends(get_session)]):
    """Estado de conectividad de todas las bases MikroTik."""
    bases = session.exec(select(BaseRed)).all()
    resultado = []
    for base in bases:
        if not base.ip_vpn:
            resultado.append({
                "id": base.id,
                "nombre": base.nombre,
                "estado": "no_configurado",
                "ip_vpn": None,
            })
            continue
        try:
            estado = mikrotik_service.verificar_estado_base(session, base.id)
            resultado.append({"id": base.id, "nombre": base.nombre, "estado": estado, "ip_vpn": base.ip_vpn})
        except Exception as e:
            resultado.append({"id": base.id, "nombre": base.nombre, "estado": "error", "detalle": str(e)})
    return resultado


@router.get("/online/{base_id}")
def clientes_online(
    base_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    """Lista las sesiones PPPoE activas en este momento en una base."""
    base = session.get(BaseRed, base_id)
    if not base:
        raise HTTPException(status_code=404, detail="Base no encontrada")
    try:
        return mikrotik_service.obtener_clientes_online(session, base_id)
    except Exception as e:
        _manejar_error_mikrotik(e, base.nombre)


@router.post("/cortar/{cliente_id}")
def cortar_cliente(
    cliente_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    base = session.get(BaseRed, cliente.base_id)

    try:
        resultado = mikrotik_service.cortar_cliente(session, cliente_id)
        # Actualizar estado en DB
        cliente.estado = EstadoCliente.cortado
        session.add(cliente)
        # Registrar en historial
        session.add(Historial(
            cliente_id=cliente_id,
            tipo=TipoEvento.corte,
            descripcion=f"Corte ejecutado por {usuario.nombre}",
            usuario_id=usuario.id,
        ))
        session.commit()
        return resultado
    except Exception as e:
        _manejar_error_mikrotik(e, base.nombre if base else "desconocida")


@router.post("/activar/{cliente_id}")
def activar_cliente(
    cliente_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    base = session.get(BaseRed, cliente.base_id)

    try:
        resultado = mikrotik_service.activar_cliente(session, cliente_id)
        cliente.estado = EstadoCliente.activo
        session.add(cliente)
        session.add(Historial(
            cliente_id=cliente_id,
            tipo=TipoEvento.reconexion,
            descripcion=f"Reconexión ejecutada por {usuario.nombre}",
            usuario_id=usuario.id,
        ))
        session.commit()
        return resultado
    except Exception as e:
        _manejar_error_mikrotik(e, base.nombre if base else "desconocida")


@router.post("/cambiar-plan/{cliente_id}")
def cambiar_plan(
    cliente_id: int,
    nuevo_plan_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    base = session.get(BaseRed, cliente.base_id)

    try:
        resultado = mikrotik_service.cambiar_plan_cliente(session, cliente_id, nuevo_plan_id)
        plan_anterior = cliente.plan_id
        cliente.plan_id = nuevo_plan_id
        session.add(cliente)
        session.add(Historial(
            cliente_id=cliente_id,
            tipo=TipoEvento.cambio_plan,
            descripcion=f"Plan cambiado de ID:{plan_anterior} a ID:{nuevo_plan_id} por {usuario.nombre}",
            usuario_id=usuario.id,
        ))
        session.commit()
        return resultado
    except Exception as e:
        _manejar_error_mikrotik(e, base.nombre if base else "desconocida")
