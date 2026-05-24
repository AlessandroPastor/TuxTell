from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.models.usuario import Usuario, UsuarioRead

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verificar_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def crear_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_usuario_actual(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> Usuario:
    credenciales_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        usuario_id: int = payload.get("sub")
        if usuario_id is None:
            raise credenciales_error
    except JWTError:
        raise credenciales_error

    usuario = session.get(Usuario, int(usuario_id))
    if not usuario or not usuario.activo:
        raise credenciales_error
    return usuario


@router.post("/login")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    usuario = session.exec(select(Usuario).where(Usuario.email == form_data.username)).first()
    if not usuario or not verificar_password(form_data.password, usuario.hashed_password):
        raise HTTPException(status_code=400, detail="Email o contraseña incorrectos")
    if not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario desactivado")

    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol})
    return {"access_token": token, "token_type": "bearer", "rol": usuario.rol}


@router.get("/me", response_model=UsuarioRead)
def get_me(usuario: Annotated[Usuario, Depends(get_usuario_actual)]):
    return usuario
