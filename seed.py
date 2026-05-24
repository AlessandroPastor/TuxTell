"""
Ejecutar UNA VEZ en el VPS para crear el usuario admin inicial.
Uso: python seed.py
"""
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models.usuario import Usuario, RolUsuario
from app.routers.auth import hashear_password


ADMIN_NOMBRE   = "Administrador"
ADMIN_EMAIL    = "admin@tuxtell.net"
ADMIN_PASSWORD = "cambiar_esta_clave_123"


def seed():
    create_db_and_tables()
    with Session(engine) as session:
        existe = session.exec(select(Usuario).where(Usuario.email == ADMIN_EMAIL)).first()
        if existe:
            print(f"[!] El usuario {ADMIN_EMAIL} ya existe. No se creó ninguno.")
            return

        admin = Usuario(
            nombre=ADMIN_NOMBRE,
            email=ADMIN_EMAIL,
            rol=RolUsuario.admin,
            activo=True,
            hashed_password=hashear_password(ADMIN_PASSWORD),
        )
        session.add(admin)

        # Crear las 3 bases (sin IP aún — se configuran cuando WireGuard esté activo)
        from app.models.base import BaseRed
        bases = [
            BaseRed(nombre="Cabanillas", ubicacion="Cabanillas", ip_vpn="10.10.0.2", puerto_api=8728),
            BaseRed(nombre="Palca",      ubicacion="Palca",      ip_vpn="10.10.0.3", puerto_api=8728),
            BaseRed(nombre="Paratia",    ubicacion="Paratia",    ip_vpn="10.10.0.4", puerto_api=8728),
        ]
        for base in bases:
            existe_base = session.exec(
                select(BaseRed).where(BaseRed.nombre == base.nombre)
            ).first()
            if not existe_base:
                session.add(base)

        session.commit()
        print(f"[OK] Admin creado: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("[OK] Bases creadas: Cabanillas (10.10.0.2), Palca (10.10.0.3), Paratia (10.10.0.4)")
        print("[!] IMPORTANTE: Cambia la contraseña del admin después de entrar.")


if __name__ == "__main__":
    seed()
