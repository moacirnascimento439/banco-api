import uuid


def transferir(client, origem, destino, valor, chave=None):
    return client.post(
        "/transferencias",
        headers={"Idempotency-Key": chave or str(uuid.uuid4())},
        json={"conta_origem": origem, "conta_destino": destino, "valor": valor},
    )


def saldo(client, numero) -> str:
    return client.get(f"/contas/{numero}").json()["saldo"]


def test_transferencia_move_saldo(client, criar_conta):
    ana = criar_conta("Ana", "100.00")
    bruno = criar_conta("Bruno", "50.00")

    r = transferir(client, ana, bruno, "30.00")

    assert r.status_code == 201
    assert r.json()["status"] == "CONCLUIDA"
    assert saldo(client, ana) == "70.00"
    assert saldo(client, bruno) == "80.00"


def test_mesma_chave_nao_duplica_e_retorna_200(client, criar_conta):
    ana = criar_conta("Ana", "100.00")
    bruno = criar_conta("Bruno", "0.00")
    chave = "chave-fixa-1"

    r1 = transferir(client, ana, bruno, "40.00", chave)
    r2 = transferir(client, ana, bruno, "40.00", chave)

    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]
    assert saldo(client, ana) == "60.00"
    assert saldo(client, bruno) == "40.00"
    assert len(client.get(f"/contas/{ana}/extrato").json()) == 1


def test_mesma_chave_com_dados_diferentes_retorna_409(client, criar_conta):
    ana = criar_conta("Ana", "100.00")
    bruno = criar_conta("Bruno", "0.00")

    transferir(client, ana, bruno, "10.00", "chave-x")
    r = transferir(client, ana, bruno, "20.00", "chave-x")

    assert r.status_code == 409
    assert saldo(client, ana) == "90.00"


def test_saldo_insuficiente_retorna_422_e_nao_altera_saldos(client, criar_conta):
    ana = criar_conta("Ana", "10.00")
    bruno = criar_conta("Bruno", "0.00")

    r = transferir(client, ana, bruno, "10.01")

    assert r.status_code == 422
    assert r.json()["erro"] == "SaldoInsuficiente"
    assert saldo(client, ana) == "10.00"
    assert saldo(client, bruno) == "0.00"


def test_pode_transferir_o_saldo_exato(client, criar_conta):
    ana = criar_conta("Ana", "10.00")
    bruno = criar_conta("Bruno", "0.00")

    assert transferir(client, ana, bruno, "10.00").status_code == 201
    assert saldo(client, ana) == "0.00"


def test_conta_inexistente_retorna_404(client, criar_conta):
    ana = criar_conta("Ana", "10.00")
    assert transferir(client, ana, "99999999", "1.00").status_code == 404
    assert saldo(client, ana) == "10.00"


def test_mesma_conta_retorna_400(client, criar_conta):
    ana = criar_conta("Ana", "10.00")
    assert transferir(client, ana, ana, "1.00").status_code == 400


def test_sem_header_de_idempotencia_retorna_422(client, criar_conta):
    ana = criar_conta("Ana", "10.00")
    bruno = criar_conta("Bruno")
    r = client.post(
        "/transferencias",
        json={"conta_origem": ana, "conta_destino": bruno, "valor": "1.00"},
    )
    assert r.status_code == 422


def test_valor_zero_ou_negativo_retorna_422(client, criar_conta):
    ana = criar_conta("Ana", "10.00")
    bruno = criar_conta("Bruno")
    assert transferir(client, ana, bruno, "0").status_code == 422
    assert transferir(client, ana, bruno, "-5.00").status_code == 422


def test_centavos_sao_exatos(client, criar_conta):
    ana = criar_conta("Ana", "0.30")
    bruno = criar_conta("Bruno")

    transferir(client, ana, bruno, "0.10")
    transferir(client, ana, bruno, "0.20")

    assert saldo(client, ana) == "0.00"
    assert saldo(client, bruno) == "0.30"


def test_extrato_mostra_origem_e_destino_mais_recente_primeiro(client, criar_conta):
    ana = criar_conta("Ana", "100.00")
    bruno = criar_conta("Bruno", "100.00")

    transferir(client, ana, bruno, "10.00")
    transferir(client, bruno, ana, "5.00")

    extrato = client.get(f"/contas/{ana}/extrato").json()
    assert len(extrato) == 2
    assert extrato[0]["valor"] == "5.00"  # a mais recente vem primeiro
    assert extrato[1]["conta_origem"] == ana


def test_extrato_de_conta_inexistente_retorna_404(client):
    assert client.get("/contas/99999999/extrato").status_code == 404


def test_saude(client):
    assert client.get("/saude").json() == {"status": "ok"}
