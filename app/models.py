"""Models: cada classe vira uma tabela (SQLAlchemy ORM, estilo 2.0)."""
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.dinheiro import para_reais
from app.exceptions import SaldoInsuficiente, TransferenciaInvalida


def agora() -> datetime:
    return datetime.now(UTC)


class Conta(Base):
    __tablename__ = "contas"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    titular: Mapped[str] = mapped_column(String(100))
    saldo_centavos: Mapped[int] = mapped_column(Integer, default=0)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    @property
    def saldo(self) -> Decimal:
        return para_reais(self.saldo_centavos)

    # A regra de negocio fica no model: ninguem altera saldo "na mao".
    def debitar(self, centavos: int) -> None:
        self._validar(centavos)
        if self.saldo_centavos < centavos:
            raise SaldoInsuficiente(self.saldo_centavos, centavos)
        self.saldo_centavos -= centavos

    def creditar(self, centavos: int) -> None:
        self._validar(centavos)
        self.saldo_centavos += centavos

    @staticmethod
    def _validar(centavos: int) -> None:
        if centavos <= 0:
            raise TransferenciaInvalida("O valor deve ser maior que zero.")


class Transferencia(Base):
    __tablename__ = "transferencias"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    conta_origem_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), index=True)
    conta_destino_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), index=True)
    valor_centavos: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="CONCLUIDA")
    # UNIQUE: o proprio banco impede duas transferencias com a mesma chave.
    chave_idempotencia: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    # relationship: navegar de Transferencia para Conta sem escrever JOIN.
    origem: Mapped[Conta] = relationship(foreign_keys=[conta_origem_id])
    destino: Mapped[Conta] = relationship(foreign_keys=[conta_destino_id])

    # Propriedades usadas pelo schema de resposta (from_attributes).
    @property
    def conta_origem(self) -> str:
        return self.origem.numero

    @property
    def conta_destino(self) -> str:
        return self.destino.numero

    @property
    def valor(self) -> Decimal:
        return para_reais(self.valor_centavos)
