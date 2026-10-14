"""Coracao do projeto: a transferencia entre contas."""
import logging

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.dinheiro import para_centavos
from app.exceptions import (
    ChaveIdempotenciaConflito,
    ContaNaoEncontrada,
    ErroDominio,
    TransferenciaInvalida,
)
from app.models import Conta, Transferencia
from app.schemas import TransferenciaCreate
from app.services.contas import buscar_conta

logger = logging.getLogger(__name__)


def _buscar_por_chave(db: Session, chave: str) -> Transferencia | None:
    return db.scalar(select(Transferencia).where(Transferencia.chave_idempotencia == chave))


def _mesma_requisicao(existente: Transferencia, dados: TransferenciaCreate) -> None:
    """Mesma chave so e aceita se for a MESMA transferencia; senao, conflito (409)."""
    igual = (
        existente.conta_origem == dados.conta_origem
        and existente.conta_destino == dados.conta_destino
        and existente.valor_centavos == para_centavos(dados.valor)
    )
    if not igual:
        raise ChaveIdempotenciaConflito()


def _travar_contas(db: Session, a: str, b: str) -> dict[str, Conta]:
    """Busca as duas contas travando as linhas (SELECT ... FOR UPDATE).

    - order_by(numero): SEMPRE travamos na mesma ordem. Se A->B e B->A chegarem
      juntas, nenhuma espera pela outra em circulo (deadlock).
    - No PostgreSQL o lock funciona de verdade. O SQLite ignora FOR UPDATE
      (ele ja serializa as escritas), entao aqui ele nao muda nada: mas o codigo
      ja esta pronto para producao.
    """
    stmt = (
        select(Conta)
        .where(Conta.numero.in_([a, b]))
        .order_by(Conta.numero)
        .with_for_update()
    )
    encontradas = {c.numero: c for c in db.scalars(stmt)}
    for numero in (a, b):
        if numero not in encontradas:
            raise ContaNaoEncontrada(numero)
    return encontradas


def transferir(
    db: Session, dados: TransferenciaCreate, chave: str
) -> tuple[Transferencia, bool]:
    """Executa a transferencia. Retorna (transferencia, criada_agora).

    criada_agora=False significa que a chave ja tinha sido processada
    (idempotencia): devolvemos o resultado anterior sem mexer no dinheiro.
    """
    # 1) Idempotencia
    existente = _buscar_por_chave(db, chave)
    if existente is not None:
        _mesma_requisicao(existente, dados)
        return existente, False

    # 2) Validacoes simples
    if dados.conta_origem == dados.conta_destino:
        raise TransferenciaInvalida("Conta de origem e destino devem ser diferentes.")

    valor = para_centavos(dados.valor)

    # 3) Debito + credito + registro: ATOMICO (um unico commit no final).
    try:
        contas = _travar_contas(db, dados.conta_origem, dados.conta_destino)
        origem = contas[dados.conta_origem]
        destino = contas[dados.conta_destino]

        origem.debitar(valor)
        destino.creditar(valor)

        transferencia = Transferencia(
            origem=origem,
            destino=destino,
            valor_centavos=valor,
            chave_idempotencia=chave,
        )
        db.add(transferencia)
        db.commit()  # tudo ou nada
    except ErroDominio:
        db.rollback()  # desfaz qualquer mudanca pendente
        raise
    except IntegrityError:
        # Duas requisicoes simultaneas com a MESMA chave: o UNIQUE do banco barra a segunda.
        db.rollback()
        existente = _buscar_por_chave(db, chave)
        if existente is None:
            raise
        _mesma_requisicao(existente, dados)
        return existente, False

    logger.info(
        "transferencia %s: %s -> %s valor=%s",
        transferencia.id, dados.conta_origem, dados.conta_destino, dados.valor,
    )
    return transferencia, True


def extrato(db: Session, numero: str) -> list[Transferencia]:
    conta = buscar_conta(db, numero)
    stmt = (
        select(Transferencia)
        .where(
            or_(
                Transferencia.conta_origem_id == conta.id,
                Transferencia.conta_destino_id == conta.id,
            )
        )
        .order_by(Transferencia.criada_em.desc())
        # selectinload: carrega origem/destino em 2 consultas extras, em vez de
        # 1 consulta por linha (o famoso problema N+1).
        .options(selectinload(Transferencia.origem), selectinload(Transferencia.destino))
    )
    return list(db.scalars(stmt))
