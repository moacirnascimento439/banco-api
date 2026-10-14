"""Ponto de entrada da aplicacao.

Rodar:  fastapi dev app/main.py     (documentacao interativa em /docs)
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  (garante que os models sejam registrados)
from app.database import Base, engine
from app.exceptions import ErroDominio
from app.routers import contas, transferencias

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ao iniciar: cria as tabelas se nao existirem.
    # (Em projetos maiores, isso e feito por migracoes com Alembic.)
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Banco API",
    version="0.1.0",
    description="API didatica de contas e transferencias bancarias.",
    lifespan=lifespan,
)

app.include_router(contas.router)
app.include_router(transferencias.router)


@app.exception_handler(ErroDominio)
async def tratar_erro_dominio(request: Request, exc: ErroDominio) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"erro": type(exc).__name__, "mensagem": str(exc)},
    )


@app.get("/saude", tags=["Infra"])
def saude():
    return {"status": "ok"}
