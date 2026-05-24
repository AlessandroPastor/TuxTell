from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models.ap import AP, APCreate, APUpdate, APRead
from app.models.cliente import Cliente
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario

router = APIRouter(prefix="/aps", tags=["access_points"])


@router.get("/", response_model=List[APRead])
def listar_aps(
    session: Annotated[Session, Depends(get_session)],
    base_id: int = None,
):
    q = select(AP)
    if base_id:
        q = q.where(AP.base_id == base_id)
    return session.exec(q).all()


@router.post("/", response_model=APRead)
def crear_ap(
    data: APCreate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    ap = AP(**data.model_dump())
    session.add(ap)
    session.commit()
    session.refresh(ap)
    return ap


@router.put("/{ap_id}", response_model=APRead)
def actualizar_ap(
    ap_id: int,
    data: APUpdate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    ap = session.get(AP, ap_id)
    if not ap:
        raise HTTPException(status_code=404, detail="AP no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(ap, campo, valor)
    session.add(ap)
    session.commit()
    session.refresh(ap)
    return ap


@router.get("/{ap_id}/clientes", response_model=List[dict])
def clientes_por_ap(
    ap_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    clientes = session.exec(
        select(Cliente).where(Cliente.ap_id == ap_id, Cliente.fecha_baja == None)
    ).all()
    return [
        {"id": c.id, "nombre": f"{c.nombre} {c.apellido}", "estado": c.estado}
        for c in clientes
    ]
