"""Schemas (Pydantic): definem e VALIDAM o que entra e sai da API.

Separados dos models de proposito: o que o cliente envia/ve nao precisa ser
igual ao que esta no banco (ex.: o banco guarda centavos, a API mostra reais).
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ContaCreate(BaseModel):
    titular: str = Field(min_length=2, max_length=100)
    saldo_inicial: Decimal = Field(default=Decimal(0), ge=0, max_digits=12, decimal_places=2)


class ContaResponse(BaseModel):
    # from_attributes: permite criar o schema a partir de um objeto do SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

    numero: str
    titular: str
    saldo: Decimal


class TransferenciaCreate(BaseModel):
    conta_origem: str = Field(pattern=r"^\d{8}$")
    conta_destino: str = Field(pattern=r"^\d{8}$")
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class TransferenciaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conta_origem: str
    conta_destino: str
    valor: Decimal
    status: str
    criada_em: datetime
