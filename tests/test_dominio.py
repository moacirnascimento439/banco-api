"""Testes UNITARIOS: sem HTTP e sem banco. Rapidos e focados na regra."""
from decimal import Decimal

import pytest

from app.dinheiro import para_centavos, para_reais
from app.exceptions import SaldoInsuficiente, TransferenciaInvalida
from app.models import Conta


def nova_conta(centavos: int) -> Conta:
    return Conta(numero="00000001", titular="Ana", saldo_centavos=centavos)


def test_debitar_reduz_saldo():
    conta = nova_conta(10_000)
    conta.debitar(3_000)
    assert conta.saldo_centavos == 7_000


def test_creditar_aumenta_saldo():
    conta = nova_conta(10_000)
    conta.creditar(2_550)
    assert conta.saldo == Decimal("125.50")


def test_debitar_mais_que_o_saldo_falha_e_nao_altera():
    conta = nova_conta(1_000)
    with pytest.raises(SaldoInsuficiente):
        conta.debitar(1_001)
    assert conta.saldo_centavos == 1_000


@pytest.mark.parametrize("valor", [0, -1, -500])
def test_valor_nao_positivo_e_invalido(valor):
    conta = nova_conta(1_000)
    with pytest.raises(TransferenciaInvalida):
        conta.creditar(valor)
    with pytest.raises(TransferenciaInvalida):
        conta.debitar(valor)


def test_conversao_de_dinheiro_e_exata():
    # Com float, 0.1 + 0.2 != 0.3. Com centavos inteiros, e exato.
    assert para_centavos(Decimal("0.10")) + para_centavos(Decimal("0.20")) == para_centavos(Decimal("0.30"))
    assert para_reais(30) == Decimal("0.30")
