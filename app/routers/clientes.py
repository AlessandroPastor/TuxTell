from typing import Annotated, List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models.cliente import Cliente, ClienteCreate, ClienteUpdate, ClienteRead, EstadoCliente
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario

router = APIRouter(prefix="/clientes", tags=["clientes"])


def _get_or_404(session: Session, cliente_id: int) -> Cliente:
    cliente = session.get(Cliente, cliente_id)
    if not cliente or cliente.fecha_baja is not None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/", response_model=List[ClienteRead])
def listar_clientes(
    session: Annotated[Session, Depends(get_session)],
    base_id: Optional[int] = Query(None),
    plan_id: Optional[int] = Query(None),
    estado: Optional[EstadoCliente] = Query(None),
    buscar: Optional[str] = Query(None, description="Busca por nombre, apellido o DNI"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
):
    q = select(Cliente).where(Cliente.fecha_baja == None)
    if base_id:
        q = q.where(Cliente.base_id == base_id)
    if plan_id:
        q = q.where(Cliente.plan_id == plan_id)
    if estado:
        q = q.where(Cliente.estado == estado)
    if buscar:
        termino = f"%{buscar}%"
        q = q.where(
            (Cliente.nombre.ilike(termino))
            | (Cliente.apellido.ilike(termino))
            | (Cliente.dni.ilike(termino))
        )
    q = q.offset(offset).limit(limit)
    return session.exec(q).all()


@router.post("/", response_model=ClienteRead)
def crear_cliente(
    data: ClienteCreate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    cliente = Cliente(**data.model_dump())
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente


@router.get("/vencen-hoy", response_model=List[ClienteRead])
def vencen_hoy(session: Annotated[Session, Depends(get_session)]):
    hoy = date.today().day
    return session.exec(
        select(Cliente).where(
            Cliente.dia_corte == hoy,
            Cliente.estado == EstadoCliente.activo,
            Cliente.fecha_baja == None,
        )
    ).all()


@router.get("/vencen-pronto", response_model=List[ClienteRead])
def vencen_pronto(
    session: Annotated[Session, Depends(get_session)],
    dias: int = Query(3, ge=1, le=7),
):
    """Clientes que vencen en los próximos N días."""
    from datetime import timedelta
    dias_proximos = [(date.today() + timedelta(days=i)).day for i in range(1, dias + 1)]
    return session.exec(
        select(Cliente).where(
            Cliente.dia_corte.in_(dias_proximos),
            Cliente.estado == EstadoCliente.activo,
            Cliente.fecha_baja == None,
        )
    ).all()


@router.get("/morosos", response_model=List[ClienteRead])
def morosos(session: Annotated[Session, Depends(get_session)]):
    """Clientes con estado cortado (no pagaron después del vencimiento)."""
    return session.exec(
        select(Cliente).where(
            Cliente.estado == EstadoCliente.cortado,
            Cliente.fecha_baja == None,
        )
    ).all()


@router.get("/{cliente_id}", response_model=ClienteRead)
def obtener_cliente(
    cliente_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    return _get_or_404(session, cliente_id)


@router.put("/{cliente_id}", response_model=ClienteRead)
def actualizar_cliente(
    cliente_id: int,
    data: ClienteUpdate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    cliente = _get_or_404(session, cliente_id)
    cambios = data.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(cliente, campo, valor)
    cliente.updated_at = datetime.utcnow()
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}")
def dar_de_baja_cliente(
    cliente_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    """Soft delete — el cliente queda con estado 'baja', no se borra."""
    from app.models.usuario import RolUsuario
    if usuario.rol != RolUsuario.admin:
        raise HTTPException(status_code=403, detail="Solo admin puede dar de baja clientes")

    cliente = _get_or_404(session, cliente_id)
    cliente.estado = EstadoCliente.baja
    cliente.fecha_baja = datetime.utcnow()
    cliente.updated_at = datetime.utcnow()
    session.add(cliente)
    session.commit()
    return {"ok": True, "mensaje": f"Cliente {cliente.nombre} {cliente.apellido} dado de baja"}
