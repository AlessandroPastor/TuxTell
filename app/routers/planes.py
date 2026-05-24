from typing import Annotated, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models.plan import Plan, PlanCreate, PlanUpdate, PlanRead
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario, RolUsuario

router = APIRouter(prefix="/planes", tags=["planes"])


@router.get("/", response_model=List[PlanRead])
def listar_planes(session: Annotated[Session, Depends(get_session)]):
    return session.exec(select(Plan).where(Plan.activo == True)).all()


@router.post("/", response_model=PlanRead)
def crear_plan(
    data: PlanCreate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    if usuario.rol != RolUsuario.admin:
        raise HTTPException(status_code=403, detail="Solo admin")
    plan = Plan(**data.model_dump())
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


@router.put("/{plan_id}", response_model=PlanRead)
def actualizar_plan(
    plan_id: int,
    data: PlanUpdate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    if usuario.rol != RolUsuario.admin:
        raise HTTPException(status_code=403, detail="Solo admin")
    plan = session.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(plan, campo, valor)
    plan.updated_at = datetime.utcnow()
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan
