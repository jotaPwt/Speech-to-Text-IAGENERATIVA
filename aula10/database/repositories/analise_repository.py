from typing import List, Optional

from sqlalchemy import delete

from config.database import get_db_session
from config.logger import get_logger
from database.models.analise_model import Analise, Transcricao

logger = get_logger(__name__)


class AnaliseRepository:
    """
    Repositório responsável por toda a persistência da entidade Analise (tabela 'analises').
    Isola completamente a camada de serviço/controller do SQLAlchemy.
    """

    def criar(self, dados: dict) -> Optional[dict]:
        try:
            with get_db_session() as session:
                nova_analise = Analise(**dados)
                session.add(nova_analise)
                session.flush()
                session.refresh(nova_analise)
                resultado = nova_analise.to_dict()
                logger.info(f"Análise criada com sucesso. ID={resultado['id']}")
                return resultado
        except Exception as e:
            logger.error(f"Erro ao criar análise no banco de dados: {e}")
            return None

    def listar_todas(self) -> List[dict]:
        try:
            with get_db_session() as session:
                registros = session.query(Analise).order_by(Analise.criado_em.desc()).all()
                return [registro.to_dict() for registro in registros]
        except Exception as e:
            logger.error(f"Erro ao listar análises: {e}")
            return []

    def buscar_por_id(self, analise_id: int) -> Optional[dict]:
        try:
            with get_db_session() as session:
                registro = session.query(Analise).filter(Analise.id == analise_id).first()
                return registro.to_dict() if registro else None
        except Exception as e:
            logger.error(f"Erro ao buscar análise ID={analise_id}: {e}")
            return None

    def buscar_caminho_imagem(self, analise_id: int) -> Optional[str]:
        try:
            with get_db_session() as session:
                registro = session.query(Analise).filter(Analise.id == analise_id).first()
                return registro.caminho_imagem if registro else None
        except Exception as e:
            logger.error(f"Erro ao buscar caminho da imagem para ID={analise_id}: {e}")
            return None

    def excluir(self, analise_id: int) -> bool:
        try:
            with get_db_session() as session:
                stmt = delete(Analise).where(Analise.id == analise_id)
                resultado = session.execute(stmt)
                sucesso = resultado.rowcount > 0
                if sucesso:
                    logger.info(f"Análise ID={analise_id} excluída com sucesso do banco de dados.")
                else:
                    logger.warning(f"Nenhuma análise encontrada para exclusão. ID={analise_id}")
                return sucesso
        except Exception as e:
            logger.error(f"Erro ao excluir análise ID={analise_id}: {e}")
            return False


class TranscricaoRepository:
    """
    Repositório responsável por toda a persistência da entidade Transcricao (tabela 'transcricoes').
    """

    def criar(self, dados: dict) -> Optional[dict]:
        try:
            with get_db_session() as session:
                nova_transcricao = Transcricao(**dados)
                session.add(nova_transcricao)
                session.flush()
                session.refresh(nova_transcricao)
                resultado = nova_transcricao.to_dict()
                logger.info(f"Transcrição criada com sucesso. ID={resultado['id']}")
                return resultado
        except Exception as e:
            logger.error(f"Erro ao criar transcrição no banco de dados: {e}")
            return None

    def listar_todas(self) -> List[dict]:
        try:
            with get_db_session() as session:
                registros = session.query(Transcricao).order_by(Transcricao.criado_em.desc()).all()
                return [registro.to_dict() for registro in registros]
        except Exception as e:
            logger.error(f"Erro ao listar transcrições: {e}")
            return []

    def buscar_por_id(self, transcricao_id: int) -> Optional[dict]:
        try:
            with get_db_session() as session:
                registro = session.query(Transcricao).filter(Transcricao.id == transcricao_id).first()
                return registro.to_dict() if registro else None
        except Exception as e:
            logger.error(f"Erro ao buscar transcrição ID={transcricao_id}: {e}")
            return None

    def excluir(self, transcricao_id: int) -> bool:
        try:
            with get_db_session() as session:
                stmt = delete(Transcricao).where(Transcricao.id == transcricao_id)
                resultado = session.execute(stmt)
                sucesso = resultado.rowcount > 0
                if sucesso:
                    logger.info(f"Transcrição ID={transcricao_id} excluída com sucesso do banco de dados.")
                else:
                    logger.warning(f"Nenhuma transcrição encontrada para exclusão. ID={transcricao_id}")
                return sucesso
        except Exception as e:
            logger.error(f"Erro ao excluir transcrição ID={transcricao_id}: {e}")
            return False
