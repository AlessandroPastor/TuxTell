from typing import Annotated, List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app.database import get_session
from app.models.pago import Pago, PagoCreate, PagoRead
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.get("/", response_model=List[PagoRead])
def listar_pagos(
    session: Annotated[Session, Depends(get_session)],
    cliente_id: Optional[int] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
):
    q = select(Pago)
    if cliente_id:
        q = q.where(Pago.cliente_id == cliente_id)
    q = q.order_by(Pago.fecha_pago.desc()).offset(offset).limit(limit)
    return session.exec(q).all()


@router.post("/", response_model=PagoRead)
def registrar_pago(
    data: PagoCreate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    from app.models.cliente import Cliente, EstadoCliente
    cliente = session.get(Cliente, data.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    pago = Pago(**data.model_dump(), registrado_por_id=usuario.id)
    session.add(pago)

    # Reactivar cliente si estaba cortado
    if cliente.estado == EstadoCliente.cortado:
        cliente.estado = EstadoCliente.activo
        session.add(cliente)

    session.commit()
    session.refresh(pago)
    return pago


@router.get("/reporte-mensual")
def reporte_mensual(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
    anio: int = Query(date.today().year),
    mes: int = Query(date.today().month, ge=1, le=12),
):
    mes_inicio = date(anio, mes, 1)
    pagos = session.exec(
        select(Pago).where(Pago.mes_correspondiente == mes_inicio)
    ).all()
    total = sum(p.monto for p in pagos)
    return {
        "mes": f"{anio}-{mes:02d}",
        "total_pagos": len(pagos),
        "total_ingresos": total,
        "pagos": [PagoRead.model_validate(p) for p in pagos],
    }


@router.get("/por-base/{base_id}")
def reporte_por_base(
    base_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
    anio: int = Query(date.today().year),
    mes: int = Query(date.today().month, ge=1, le=12),
):
    from app.models.cliente import Cliente
    mes_inicio = date(anio, mes, 1)
    pagos = session.exec(
        select(Pago)
        .join(Cliente, Pago.cliente_id == Cliente.id)
        .where(Cliente.base_id == base_id, Pago.mes_correspondiente == mes_inicio)
    ).all()
    total = sum(p.monto for p in pagos)
    return {"base_id": base_id, "mes": f"{anio}-{mes:02d}", "total": total, "cantidad": len(pagos)}
