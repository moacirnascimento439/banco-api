"""Configuracao lida de variaveis de ambiente (com valor padrao para desenvolvimento)."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./banco.db")
