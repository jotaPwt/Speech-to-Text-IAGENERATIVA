import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config.logger import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError(
        "A variável de ambiente DATABASE_URL não foi definida. "
        "Configure a string de conexão do Neon.tech (ex: postgresql://user:pass@host/dbname?sslmode=require)."
    )

# Garante o driver correto para SQLAlchemy 2.x usando Psycopg 3 (psycopg)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Limpa o sufixo antigo caso ele venha configurado incorretamente
if "+psycopg2" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+psycopg2", "+psycopg")

# Configuração crítica de resiliência para o pooler (PgBouncer) do Neon.tech.
engine = create_engine(
    DATABASE_URL,
    pool_size=0,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def get_db_session():
    """
    Context manager que garante abertura, commit/rollback e fechamento
    seguro da sessão do banco de dados em toda a aplicação.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erro na sessão do banco de dados, rollback executado: {e}")
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Cria todas as tabelas mapeadas caso ainda não existam no banco.
    Deve ser chamada uma única vez na inicialização da aplicação.
    """
    from database.models.analise_model import Analise, Transcricao  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas 'analises' e 'transcricoes' criadas/verificadas com sucesso no Neon.tech.")
