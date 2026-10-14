"""Dinheiro: guardamos CENTAVOS (int) no banco.

Por que nao float? 0.1 + 0.2 == 0.30000000000000004 em float.
Com inteiros (centavos) a conta e sempre exata.
Na API usamos Decimal (reais com 2 casas) e convertemos aqui.
"""
from decimal import ROUND_HALF_EVEN, Decimal


def para_centavos(valor: Decimal) -> int:
    return int((valor * 100).to_integral_value(rounding=ROUND_HALF_EVEN))


def para_reais(centavos: int) -> Decimal:
    return (Decimal(centavos) / 100).quantize(Decimal("0.01"))
