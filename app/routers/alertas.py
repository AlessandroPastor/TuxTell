"""
Alertas WhatsApp — skeleton listo para conectar con Evolution API o Twilio.
La lógica de envío se implementa en services/whatsapp_service.py cuando
se defina el proveedor.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date, timedelta

from app.database import get_session
from app.models.cliente import Cliente, EstadoCliente
from app.routers.auth import get_usuario_actual
from app.models.usuario import Usuario

router = APIRouter(prefix="/alertas", tags=["alertas"])


def _mensaje_vencimiento(cliente: Cliente, dias_restantes: int) -> str:
    if dias_restantes == 0:
        return (
            f"Hola {cliente.nombre}, tu servicio de internet vence HOY. "
            f"Realiza tu pago para no quedarte sin internet. "
            f"Yape: 936511008 - tuxtell.net"
        )
    return (
        f"Hola {cliente.nombre}, tu servicio de internet vence el día {cliente.dia_corte}. "
        f"Tienes {dias_restantes} día(s) para renovar. "
        f"Yape: 936511008 - tuxtell.net"
    )


async def _enviar_whatsapp(telefono: str, mensaje: str) -> dict:
    """
    Placeholder — implementar con Evolution API o Twilio.
    Por ahora retorna el mensaje que se enviaría.
    """
    from app.config import settings
    if not settings.whatsapp_api_key:
        return {"simulado": True, "telefono": telefono, "mensaje": mensaje}

    # TODO: implementar según proveedor configurado en settings.whatsapp_provider
    raise NotImplementedError("Configura WHATSAPP_PROVIDER y WHATSAPP_API_KEY en .env")


@router.post("/enviar-whatsapp/{cliente_id}")
async def enviar_whatsapp_cliente(
    cliente_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
):
    """Envía manualmente un recordatorio de pago al cliente."""
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    hoy = date.today().day
    dias = cliente.dia_corte - hoy
    if dias < 0:
        dias = 0

    mensaje = _mensaje_vencimiento(cliente, dias)
    resultado = await _enviar_whatsapp(cliente.telefono, mensaje)
    return {"ok": True, "resultado": resultado}


@router.get("/pendientes")
def alertas_pendientes(session: Annotated[Session, Depends(get_session)]):
    """
    Lista los clientes que deberían recibir alerta hoy:
    - vencen hoy
    - vencen en 3 días
    """
    hoy = date.today().day
    dia_3 = (date.today() + timedelta(days=3)).day

    vencen_hoy = session.exec(
        select(Cliente).where(
            Cliente.dia_corte == hoy,
            Cliente.estado == EstadoCliente.activo,
            Cliente.fecha_baja == None,
        )
    ).all()

    vencen_3dias = session.exec(
        select(Cliente).where(
            Cliente.dia_corte == dia_3,
            Cliente.estado == EstadoCliente.activo,
            Cliente.fecha_baja == None,
        )
    ).all()

    return {
        "vencen_hoy": [
            {"id": c.id, "nombre": f"{c.nombre} {c.apellido}", "telefono": c.telefono}
            for c in vencen_hoy
        ],
        "vencen_en_3_dias": [
            {"id": c.id, "nombre": f"{c.nombre} {c.apellido}", "telefono": c.telefono}
            for c in vencen_3dias
        ],
    }
