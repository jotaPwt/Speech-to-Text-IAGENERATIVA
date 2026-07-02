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

# Garante o driver correto para SQLAlchemy 2.x, mesmo que a URL venha no formato antigo do Neon/Heroku
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg2" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Configuração crítica de resiliência para o pooler (PgBouncer) do Neon.tech.
# pool_size=0 e max_overflow=0 fazem o SQLAlchemy não manter conexões próprias
# em cache, delegando totalmente o pooling ao PgBouncer do Neon, evitando
# erros de "prepared statement already exists" e conexões zumbis.
# pool_pre_ping=True testa a conexão antes de cada uso, evitando falhas
# por conexões que o pooler já derrubou silenciosamente.
engine = create_engine(
    DATABASE_URL,
    pool_size=0,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
    },
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
