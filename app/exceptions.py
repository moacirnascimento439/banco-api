"""Erros de dominio: representam regras de negocio violadas.

O service lanca esses erros; o main.py os converte em respostas HTTP.
Assim a regra de negocio nao depende de detalhes de HTTP (a nao ser pelo
status_code padrao, que deixamos aqui por simplicidade didatica).
"""


class ErroDominio(Exception):
    status_code = 400


class ContaNaoEncontrada(ErroDominio):
    status_code = 404

    def __init__(self, numero: str):
        super().__init__(f"Conta nao encontrada: {numero}")


class SaldoInsuficiente(ErroDominio):
    status_code = 422

    def __init__(self, saldo_centavos: int, valor_centavos: int):
        super().__init__(
            f"Saldo insuficiente: saldo {saldo_centavos / 100:.2f}, "
            f"valor solicitado {valor_centavos / 100:.2f}"
        )


class TransferenciaInvalida(ErroDominio):
    status_code = 400


class ChaveIdempotenciaConflito(ErroDominio):
    status_code = 409

    def __init__(self):
        super().__init__(
            "Essa Idempotency-Key ja foi usada em uma transferencia diferente."
        )
