import os
from typing import List, Optional, Dict, Any

from services.vision_service import VisionService
from database.repositories.analise_repository import AnaliseRepository
from config.logger import get_logger

logger = get_logger(__name__)


class AnaliseController:
    """
    Orquestra o fluxo entre a camada de apresentação (Streamlit), o serviço
    de Visão Computacional e o repositório de persistência das análises.
    """

    def __init__(self):
        self.vision_service = VisionService()
        self.repository = AnaliseRepository()

    def processar_e_salvar(self, bytes_imagem: bytes, nome_original: str = "captura.jpg") -> Optional[Dict[str, Any]]:
        try:
            dados_processados = self.vision_service.processar_imagem(bytes_imagem, nome_original)
            resultado = self.repository.criar(dados_processados)
            return resultado
        except Exception as e:
            logger.error(f"Erro no controller ao processar e salvar imagem: {e}")
            return None

    def listar_historico(self) -> List[Dict[str, Any]]:
        return self.repository.listar_todas()

    def excluir_analise(self, analise_id: int) -> bool:
        caminho_imagem = self.repository.buscar_caminho_imagem(analise_id)
        excluido_banco = self.repository.excluir(analise_id)

        if excluido_banco and caminho_imagem and os.path.exists(caminho_imagem):
            try:
                os.remove(caminho_imagem)
                logger.info(f"Arquivo físico removido do disco: {caminho_imagem}")
            except OSError as e:
                logger.warning(f"Não foi possível remover o arquivo físico {caminho_imagem}: {e}")

        return excluido_banco

    def obter_caminho_imagem(self, analise_id: int) -> Optional[str]:
        return self.repository.buscar_caminho_imagem(analise_id)
