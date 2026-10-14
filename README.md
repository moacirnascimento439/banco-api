# Banco API

API REST de contas e transferencias bancarias, feita para **aprender backend com Python na pratica**
e servir de projeto de portfolio. Stack: **FastAPI + SQLAlchemy 2 + Pydantic v2 + SQLite + pytest**.

## Como rodar (GitHub Codespaces)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

pytest -q                    # roda os testes (devem passar todos)
fastapi dev app/main.py      # sobe a API; abra a porta 8000 na aba PORTS e va em /docs
```

Se abrir via `.devcontainer`, as dependencias ja sao instaladas sozinhas.

## Endpoints

| Metodo | Rota | O que faz |
|---|---|---|
| POST | /contas | Cria conta (201; numero de 8 digitos gerado) |
| GET | /contas?limit=&offset= | Lista contas com paginacao |
| GET | /contas/{numero} | Consulta saldo |
| GET | /contas/{numero}/extrato | Transferencias da conta (mais recentes primeiro) |
| POST | /transferencias | Transfere. Header `Idempotency-Key` obrigatorio. 201 na 1a vez, 200 se repetir a mesma chave |
| GET | /saude | Health check |

Erros: 404 (conta nao existe), 422 (validacao ou saldo insuficiente), 400 (mesma conta), 409 (chave de idempotencia reutilizada com dados diferentes).

## Teste manual com curl

```bash
curl -s -X POST localhost:8000/contas -H 'Content-Type: application/json' \
  -d '{"titular":"Ana","saldo_inicial":100.00}'
curl -s -X POST localhost:8000/contas -H 'Content-Type: application/json' \
  -d '{"titular":"Bruno","saldo_inicial":50.00}'

curl -s -i -X POST localhost:8000/transferencias \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: abc-1' \
  -d '{"conta_origem":"NUMERO_ANA","conta_destino":"NUMERO_BRUNO","valor":30.00}'
# repita o comando acima: volta 200 e o saldo NAO muda
```

## Estrutura

```
app/
  main.py            entrada, rotas registradas, handler de erros
  config.py          configuracao por variavel de ambiente
  database.py        engine, sessao, dependencia get_db
  models.py          tabelas (Conta, Transferencia) + regra de saldo
  schemas.py         validacao de entrada/saida (Pydantic)
  dinheiro.py        conversao reais <-> centavos
  exceptions.py      erros de dominio
  routers/           camada HTTP (fina)
  services/          regras de negocio (sem HTTP)
tests/               unitarios (dominio) + integracao (API)
```

Fluxo: `HTTP -> router -> service -> model/banco`. O router nao tem regra de negocio; o service nao conhece HTTP.

## Decisoes para entender (e explicar em entrevista)

1. **Centavos inteiros** no banco, **Decimal** na API: nunca float para dinheiro.
2. **Transacao unica**: debito + credito + registro acontecem num unico `commit` (tudo ou nada).
3. **Idempotency-Key**: reenviar a requisicao nao duplica a transferencia; o UNIQUE do banco protege tambem em corrida.
4. **Travamento em ordem fixa** (`FOR UPDATE` + `ORDER BY numero`): evita deadlock em A->B e B->A simultaneas. O SQLite ignora `FOR UPDATE`; em PostgreSQL ele passa a valer.
5. **Schemas separados dos models**: a API nao e refem da estrutura do banco.
6. **selectinload** no extrato: evita o problema N+1.
7. **Testes isolados**: cada teste usa um banco SQLite em memoria novo (`dependency_overrides`).

## Roadmap (cada fase vira commits e PRs no seu GitHub)

- **Fase 1 - Entender**: siga a aba *Roteiro* da planilha: ler, rodar, quebrar, reescrever.
- **Fase 2 - Estender**: limite por transferencia, deposito, estorno, filtros e paginacao do extrato.
- **Fase 3 - Seguranca**: usuarios, hash de senha, login JWT, cada usuario so acessa suas contas.
- **Fase 4 - Producao**: Alembic, PostgreSQL com Docker Compose, Dockerfile, CI verde, deploy.

## Limitacoes conhecidas (de proposito, viram exercicios)

- Sem autenticacao (Fase 3).
- `create_all` no startup em vez de migracoes (Fase 4).
- Sem testes de concorrencia reais (exigem banco com lock, como PostgreSQL).
