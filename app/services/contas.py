"""Regras de negocio de contas. Sem HTTP aqui: so Python e banco."""
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dinheiro import para_centavos
from app.exceptions import ContaNaoEncontrada
from app.models import Conta
from app.schemas import ContaCreate


def _gerar_numero() -> str:
    return f"{secrets.randbelow(10**8):08d}"


def criar_conta(db: Session, dados: ContaCreate) -> Conta:
    # Gera um numero que ainda nao existe (tenta algumas vezes).
    for _ in range(5):
        numero = _gerar_numero()
        if db.scalar(select(Conta.id).where(Conta.numero == numero)) is None:
            break
    else:
        raise RuntimeError("Nao foi possivel gerar numero de conta unico.")

    conta = Conta(
        numero=numero,
        titular=dados.titular.strip(),
        saldo_centavos=para_centavos(dados.saldo_inicial),
    )
    db.add(conta)
    db.commit()
    return conta


def buscar_conta(db: Session, numero: str) -> Conta:
    conta = db.scalar(select(Conta).where(Conta.numero == numero))
    if conta is None:
        raise ContaNaoEncontrada(numero)
    return conta


def listar_contas(db: Session, limit: int, offset: int) -> list[Conta]:
    stmt = select(Conta).order_by(Conta.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))
