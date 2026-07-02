from typing import List, Optional, Dict, Any

from services.stt_service import STTService
from database.repositories.analise_repository import TranscricaoRepository
from config.logger import get_logger

logger = get_logger(__name__)


class AudioController:
    """
    Orquestra o fluxo entre a camada de apresentação (Streamlit), o serviço
    de Speech-to-Text e o repositório de persistência das transcrições.
    """

    def __init__(self):
        self.stt_service = STTService()
        self.repository = TranscricaoRepository()

    def processar_e_salvar(self, bytes_audio: bytes, nome_original: str = "gravacao.wav") -> Optional[Dict[str, Any]]:
        try:
            dados_transcricao = self.stt_service.transcrever(bytes_audio, nome_original)
            resultado = self.repository.criar(dados_transcricao)
            return resultado
        except Exception as e:
            logger.error(f"Erro no controller ao processar e salvar áudio: {e}")
            return None

    def listar_historico(self) -> List[Dict[str, Any]]:
        return self.repository.listar_todas()

    def excluir_transcricao(self, transcricao_id: int) -> bool:
        return self.repository.excluir(transcricao_id)
