"""
Servicio MikroTik — lee IPs dinámicamente desde la DB.
Cuando la infraestructura no esté lista, los métodos retornan
MikrotikNoConfigurado en lugar de crashear la app.
"""
import socket
from contextlib import contextmanager
from typing import Optional
from sqlmodel import Session, select

from app.models.base import BaseRed, EstadoBase


class MikrotikNoConfigurado(Exception):
    """La base no tiene ip_vpn ni credenciales configuradas aún."""


class MikrotikOffline(Exception):
    """La base está configurada pero no responde."""


class MikrotikError(Exception):
    """Error al ejecutar un comando en el MikroTik."""


def _verificar_ip_configurada(base: BaseRed) -> None:
    if not base.ip_vpn or not base.usuario_api or not base.clave_api:
        raise MikrotikNoConfigurado(
            f"La base '{base.nombre}' no tiene IP ni credenciales configuradas. "
            f"Actualiza ip_vpn, usuario_api y clave_api en la tabla bases."
        )


@contextmanager
def _conexion_routeros(ip: str, usuario: str, clave: str, puerto: int = 8728):
    """Abre y cierra la conexión RouterOS API de forma segura."""
    try:
        import librouteros
        api = librouteros.connect(
            host=ip,
            username=usuario,
            password=clave,
            port=puerto,
            timeout=5,
        )
        try:
            yield api
        finally:
            api.close()
    except ImportError:
        raise MikrotikError("librouteros no está instalado. Ejecuta: pip install librouteros")
    except socket.timeout:
        raise MikrotikOffline(f"Timeout conectando a {ip}:{puerto}. ¿Está el túnel WireGuard activo?")
    except Exception as e:
        raise MikrotikError(f"Error conectando a {ip}: {e}")


# ─────────────────────────────────────────────────────────────────
# FUNCIONES PÚBLICAS — reciben session de DB y base_id
# ─────────────────────────────────────────────────────────────────

def verificar_estado_base(session: Session, base_id: int) -> EstadoBase:
    """Verifica si el MikroTik de una base responde. Actualiza el campo estado."""
    base = session.get(BaseRed, base_id)
    if not base:
        raise ValueError(f"Base con id={base_id} no existe.")

    if not base.ip_vpn:
        return EstadoBase.desconocido

    try:
        with _conexion_routeros(base.ip_vpn, base.usuario_api, base.clave_api, base.puerto_api):
            from datetime import datetime
            base.estado = EstadoBase.online
            base.ultima_verificacion = datetime.utcnow()
            session.add(base)
            session.commit()
            return EstadoBase.online
    except (MikrotikOffline, MikrotikError):
        base.estado = EstadoBase.offline
        session.add(base)
        session.commit()
        return EstadoBase.offline


def cortar_cliente(session: Session, cliente_id: int) -> dict:
    """
    Deshabilita el usuario PPPoE del cliente en su MikroTik base.
    Retorna dict con resultado.
    """
    from app.models.cliente import Cliente
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise ValueError(f"Cliente {cliente_id} no encontrado.")
    if not cliente.usuario_pppoe:
        raise MikrotikError(f"Cliente {cliente_id} no tiene usuario PPPoE configurado.")

    base = session.get(BaseRed, cliente.base_id)
    _verificar_ip_configurada(base)

    with _conexion_routeros(base.ip_vpn, base.usuario_api, base.clave_api, base.puerto_api) as api:
        # Deshabilitar usuario PPPoE
        users = list(api(cmd="/ppp/secret/print", **{"?name": cliente.usuario_pppoe}))
        if not users:
            raise MikrotikError(f"Usuario PPPoE '{cliente.usuario_pppoe}' no existe en el MikroTik.")
        api(cmd="/ppp/secret/set", **{"=.id": users[0][".id"], "=disabled": "yes"})

        # Remover sesión activa si existe
        sessions = list(api(cmd="/ppp/active/print", **{"?name": cliente.usuario_pppoe}))
        for s in sessions:
            try:
                api(cmd="/ppp/active/remove", **{"=.id": s[".id"]})
            except Exception:
                pass

    return {"ok": True, "mensaje": f"Cliente {cliente.nombre} {cliente.apellido} cortado en {base.nombre}"}


def activar_cliente(session: Session, cliente_id: int) -> dict:
    """Habilita el usuario PPPoE del cliente en su MikroTik base."""
    from app.models.cliente import Cliente
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise ValueError(f"Cliente {cliente_id} no encontrado.")
    if not cliente.usuario_pppoe:
        raise MikrotikError(f"Cliente {cliente_id} no tiene usuario PPPoE configurado.")

    base = session.get(BaseRed, cliente.base_id)
    _verificar_ip_configurada(base)

    with _conexion_routeros(base.ip_vpn, base.usuario_api, base.clave_api, base.puerto_api) as api:
        users = list(api(cmd="/ppp/secret/print", **{"?name": cliente.usuario_pppoe}))
        if not users:
            raise MikrotikError(f"Usuario PPPoE '{cliente.usuario_pppoe}' no existe en el MikroTik.")
        api(cmd="/ppp/secret/set", **{"=.id": users[0][".id"], "=disabled": "no"})

    return {"ok": True, "mensaje": f"Cliente {cliente.nombre} {cliente.apellido} activado en {base.nombre}"}


def cambiar_plan_cliente(session: Session, cliente_id: int, nuevo_plan_id: int) -> dict:
    """Cambia el profile PPPoE del cliente en el MikroTik."""
    from app.models.cliente import Cliente
    from app.models.plan import Plan
    cliente = session.get(Cliente, cliente_id)
    plan = session.get(Plan, nuevo_plan_id)
    if not cliente or not plan:
        raise ValueError("Cliente o plan no encontrado.")

    base = session.get(BaseRed, cliente.base_id)
    _verificar_ip_configurada(base)

    with _conexion_routeros(base.ip_vpn, base.usuario_api, base.clave_api, base.puerto_api) as api:
        users = list(api(cmd="/ppp/secret/print", **{"?name": cliente.usuario_pppoe}))
        if not users:
            raise MikrotikError(f"Usuario PPPoE '{cliente.usuario_pppoe}' no existe en el MikroTik.")
        # El nombre del profile en MikroTik debe coincidir con plan.nombre
        api(cmd="/ppp/secret/set", **{"=.id": users[0][".id"], "=profile": plan.nombre})

    return {"ok": True, "mensaje": f"Plan cambiado a {plan.nombre} para {cliente.nombre}"}


def crear_usuario_pppoe(session: Session, cliente_id: int) -> dict:
    """Crea el usuario PPPoE en el MikroTik de la base del cliente."""
    from app.models.cliente import Cliente
    from app.models.plan import Plan
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise ValueError(f"Cliente {cliente_id} no encontrado.")
    if not cliente.usuario_pppoe or not cliente.clave_pppoe:
        raise MikrotikError("El cliente no tiene usuario_pppoe o clave_pppoe definidos.")

    base = session.get(BaseRed, cliente.base_id)
    plan = session.get(Plan, cliente.plan_id)
    _verificar_ip_configurada(base)

    with _conexion_routeros(base.ip_vpn, base.usuario_api, base.clave_api, base.puerto_api) as api:
        api(
            cmd="/ppp/secret/add",
            **{
                "=name": cliente.usuario_pppoe,
                "=password": cliente.clave_pppoe,
                "=service": "pppoe",
                "=profile": plan.nombre if plan else "default",
                "=comment": f"Cliente ID:{cliente.id} - {cliente.nombre} {cliente.apellido}",
            }
        )

    return {"ok": True, "mensaje": f"Usuario PPPoE '{cliente.usuario_pppoe}' creado en {base.nombre}"}


def obtener_clientes_online(session: Session, base_id: int) -> list[dict]:
    """Retorna la lista de sesiones PPPoE activas en una base."""
    base = session.get(BaseRed, base_id)
    _verificar_ip_configurada(base)

    with _conexion_routeros(base.ip_vpn, base.usuario_api, base.clave_api, base.puerto_api) as api:
        sessions = list(api(cmd="/ppp/active/print"))
        return [
            {
                "usuario": s.get("name"),
                "ip_asignada": s.get("address"),
                "uptime": s.get("uptime"),
                "llamada_desde": s.get("caller-id"),
            }
            for s in sessions
        ]
