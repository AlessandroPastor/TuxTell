from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
    **({} if _is_sqlite else {"pool_pre_ping": True}),
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
