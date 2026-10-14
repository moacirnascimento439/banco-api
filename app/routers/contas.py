"""Rotas HTTP de contas. Camada fina: recebe, delega ao service e responde."""
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.database import DbSession
from app.schemas import ContaCreate, ContaResponse, TransferenciaResponse
from app.services import contas, transferencias

router = APIRouter(prefix="/contas", tags=["Contas"])


@router.post("", response_model=ContaResponse, status_code=201)
def criar(dados: ContaCreate, response: Response, db: DbSession):
    conta = contas.criar_conta(db, dados)
    response.headers["Location"] = f"/contas/{conta.numero}"
    return conta


@router.get("", response_model=list[ContaResponse])
def listar(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return contas.listar_contas(db, limit, offset)


@router.get("/{numero}", response_model=ContaResponse)
def buscar(numero: str, db: DbSession):
    return contas.buscar_conta(db, numero)


@router.get("/{numero}/extrato", response_model=list[TransferenciaResponse])
def extrato(numero: str, db: DbSession):
    return transferencias.extrato(db, numero)
