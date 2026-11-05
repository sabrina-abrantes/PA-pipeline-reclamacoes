"""Configuração compartilhada: lê o .env e abre conexão com o PostgreSQL."""
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

RAW_DIR = RAIZ / os.getenv("RAW_DIR", "data/raw")
LOGS_DIR = RAIZ / "logs"
REPORTS_DIR = RAIZ / "reports"
DOCS_DIR = RAIZ / "docs"

TABELA_RAW = "raw.reclamacoes"


def conectar():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        user=os.getenv("PG_USER", "pa"),
        password=os.getenv("PG_PASSWORD", ""),
        dbname=os.getenv("PG_DB", "reclamacoes"),
    )
