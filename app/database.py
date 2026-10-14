"""Conexao com o banco e sessao por requisicao.

- engine: gerencia a conexao com o banco.
- SessionLocal: fabrica de sessoes (uma sessao = uma "conversa" com o banco).
- get_db: dependencia do FastAPI. Abre uma sessao ao comecar a requisicao
  e SEMPRE fecha ao terminar (mesmo com erro).
"""
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL

# SQLite precisa desse argumento para ser usado com varias threads (FastAPI usa).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe base de todos os models (tabelas)."""


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Atalho para usar nas rotas: def rota(db: DbSession)
DbSession = Annotated[Session, Depends(get_db)]
