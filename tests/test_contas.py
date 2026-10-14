def test_criar_conta(client):
    r = client.post("/contas", json={"titular": "Ana", "saldo_inicial": "100.00"})
    assert r.status_code == 201
    corpo = r.json()
    assert len(corpo["numero"]) == 8
    assert corpo["titular"] == "Ana"
    assert corpo["saldo"] == "100.00"
    assert r.headers["location"] == f"/contas/{corpo['numero']}"


def test_saldo_inicial_padrao_e_zero(client):
    r = client.post("/contas", json={"titular": "Bruno"})
    assert r.status_code == 201
    assert r.json()["saldo"] == "0.00"


def test_titular_muito_curto_retorna_422(client):
    r = client.post("/contas", json={"titular": "A"})
    assert r.status_code == 422


def test_saldo_negativo_retorna_422(client):
    r = client.post("/contas", json={"titular": "Ana", "saldo_inicial": "-1"})
    assert r.status_code == 422


def test_mais_de_duas_casas_decimais_retorna_422(client):
    r = client.post("/contas", json={"titular": "Ana", "saldo_inicial": "10.123"})
    assert r.status_code == 422


def test_buscar_conta(client, criar_conta):
    numero = criar_conta("Ana", "50.00")
    r = client.get(f"/contas/{numero}")
    assert r.status_code == 200
    assert r.json()["saldo"] == "50.00"


def test_buscar_conta_inexistente_retorna_404(client):
    r = client.get("/contas/99999999")
    assert r.status_code == 404
    assert r.json()["erro"] == "ContaNaoEncontrada"


def test_listar_contas_com_paginacao(client, criar_conta):
    for nome in ("Ana", "Bruno", "Carla"):
        criar_conta(nome)
    r = client.get("/contas", params={"limit": 2, "offset": 0})
    assert r.status_code == 200
    assert len(r.json()) == 2
    r = client.get("/contas", params={"limit": 2, "offset": 2})
    assert len(r.json()) == 1
