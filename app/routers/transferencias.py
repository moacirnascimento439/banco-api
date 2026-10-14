from typing import Annotated

from fastapi import APIRouter, Header, Response

from app.database import DbSession
from app.schemas import TransferenciaCreate, TransferenciaResponse
from app.services import transferencias

router = APIRouter(prefix="/transferencias", tags=["Transferencias"])


@router.post("", response_model=TransferenciaResponse, status_code=201)
def transferir(
    dados: TransferenciaCreate,
    response: Response,
    db: DbSession,
    # Header "Idempotency-Key" (FastAPI troca _ por - automaticamente).
    idempotency_key: Annotated[str, Header(min_length=1, max_length=100)],
):
    """Cria uma transferencia. Reenviar a mesma chave NAO duplica: devolve 200."""
    transferencia, criada = transferencias.transferir(db, dados, idempotency_key)
    if not criada:
        response.status_code = 200
    return transferencia
