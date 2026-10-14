import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    """Cliente de teste com um banco SQLite NOVO e em memoria para cada teste."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # mantem a mesma conexao (banco em memoria some se fechar)
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    # Troca a dependencia real pela de teste.
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def criar_conta(client):
    """Fabrica de contas: criar_conta('Ana', '100.00') -> numero."""

    def _criar(titular: str = "Ana", saldo: str = "0.00") -> str:
        r = client.post("/contas", json={"titular": titular, "saldo_inicial": saldo})
        assert r.status_code == 201, r.text
        return r.json()["numero"]

    return _criar
