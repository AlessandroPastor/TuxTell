from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from datetime import date

from app.database import get_session
from app.models.pago import Pago
from app.models.cliente import Cliente
from app.models.plan import Plan
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/ingresos-mes")
def ingresos_mes(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
    anio: int = Query(date.today().year),
    mes: int = Query(date.today().month, ge=1, le=12),
):
    mes_inicio = date(anio, mes, 1)
    pagos = session.exec(select(Pago).where(Pago.mes_correspondiente == mes_inicio)).all()
    return {
        "mes": f"{anio}-{mes:02d}",
        "total": sum(p.monto for p in pagos),
        "cantidad_pagos": len(pagos),
        "por_metodo": {
            "yape": sum(p.monto for p in pagos if p.metodo == "yape"),
            "transferencia": sum(p.monto for p in pagos if p.metodo == "transferencia"),
            "efectivo": sum(p.monto for p in pagos if p.metodo == "efectivo"),
        },
    }


@router.get("/ingresos-base")
def ingresos_por_base(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
    anio: int = Query(date.today().year),
    mes: int = Query(date.today().month, ge=1, le=12),
):
    from app.models.base import BaseRed
    mes_inicio = date(anio, mes, 1)
    bases = session.exec(select(BaseRed)).all()
    resultado = []
    for base in bases:
        pagos = session.exec(
            select(Pago)
            .join(Cliente, Pago.cliente_id == Cliente.id)
            .where(Cliente.base_id == base.id, Pago.mes_correspondiente == mes_inicio)
        ).all()
        resultado.append({
            "base": base.nombre,
            "total": sum(p.monto for p in pagos),
            "cantidad": len(pagos),
        })
    return resultado


@router.get("/clientes-por-plan")
def clientes_por_plan(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    from app.models.cliente import EstadoCliente
    planes = session.exec(select(Plan)).all()
    resultado = []
    for plan in planes:
        total = len(session.exec(
            select(Cliente).where(Cliente.plan_id == plan.id, Cliente.fecha_baja == None)
        ).all())
        activos = len(session.exec(
            select(Cliente).where(
                Cliente.plan_id == plan.id,
                Cliente.estado == EstadoCliente.activo,
                Cliente.fecha_baja == None,
            )
        ).all())
        resultado.append({
            "plan": plan.nombre,
            "precio": plan.precio,
            "total_clientes": total,
            "activos": activos,
        })
    return resultado
