from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.routers import auth, bases, clientes, mikrotik, pagos, planes, aps, equipos, alertas, reportes

app = FastAPI(
    title="TUXTELL.NET — API ISP",
    description="Sistema de gestión para ISP con control MikroTik en tiempo real",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción, reemplazar por el dominio de la app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bases.router)
app.include_router(clientes.router)
app.include_router(mikrotik.router)
app.include_router(pagos.router)
app.include_router(planes.router)
app.include_router(aps.router)
app.include_router(equipos.router)
app.include_router(alertas.router)
app.include_router(reportes.router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {"sistema": "TUXTELL.NET", "version": "1.0.0", "estado": "ok"}


@app.get("/health")
def health():
    return {"ok": True}
