from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models.equipo import Equipo, EquipoCreate, EquipoUpdate, EquipoRead, EstadoEquipo
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario

router = APIRouter(prefix="/equipos", tags=["equipos"])


@router.get("/prestados", response_model=List[EquipoRead])
def equipos_prestados(session: Annotated[Session, Depends(get_session)]):
    """Lista todos los equipos prestados que aún están activos (no devueltos)."""
    return session.exec(
        select(Equipo).where(
            Equipo.es_prestado == True,
            Equipo.estado == EstadoEquipo.activo,
        )
    ).all()


@router.get("/{cliente_id}", response_model=List[EquipoRead])
def equipos_por_cliente(
    cliente_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    return session.exec(select(Equipo).where(Equipo.cliente_id == cliente_id)).all()


@router.post("/", response_model=EquipoRead)
def registrar_equipo(
    data: EquipoCreate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    equipo = Equipo(**data.model_dump())
    session.add(equipo)
    session.commit()
    session.refresh(equipo)
    return equipo


@router.put("/{equipo_id}", response_model=EquipoRead)
def actualizar_equipo(
    equipo_id: int,
    data: EquipoUpdate,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(equipo, campo, valor)
    session.add(equipo)
    session.commit()
    session.refresh(equipo)
    return equipo
