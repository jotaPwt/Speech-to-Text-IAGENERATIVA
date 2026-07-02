import os
import uuid
import tempfile
from datetime import datetime
from typing import Dict, Any, Tuple

import speech_recognition as sr
from pydub import AudioSegment

from config.logger import get_logger

logger = get_logger(__name__)

DIRETORIO_AUDIOS = os.path.join("assets", "audios")


class STTService:
    """
    Serviço responsável pela transcrição de áudio para texto (Speech-to-Text),
    utilizando SpeechRecognition (Google Speech API) com pré-processamento
    via pydub para garantir compatibilidade de formato (WAV mono 16kHz).
    """

    def __init__(self):
        os.makedirs(DIRETORIO_AUDIOS, exist_ok=True)
        self.recognizer = sr.Recognizer()

    def _converter_para_wav(self, bytes_audio: bytes, nome_original: str) -> Tuple[str, str, float]:
        """
        Converte o áudio recebido (qualquer formato suportado pelo ffmpeg/pydub)
        para WAV mono 16kHz, formato ideal para o SpeechRecognition, e salva
        fisicamente em assets/audios/.
        """
        extensao_original = os.path.splitext(nome_original)[1].lstrip(".").lower() or "wav"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        identificador = uuid.uuid4().hex[:8]

        with tempfile.NamedTemporaryFile(suffix=f".{extensao_original}", delete=False) as arquivo_temp:
            arquivo_temp.write(bytes_audio)
            caminho_temp_original = arquivo_temp.name

        try:
            try:
                audio_segment = AudioSegment.from_file(caminho_temp_original)
            except Exception:
                audio_segment = AudioSegment.from_file(caminho_temp_original, format="wav")

            audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)

            nome_arquivo_wav = f"audio_{timestamp}_{identificador}.wav"
            caminho_wav = os.path.join(DIRETORIO_AUDIOS, nome_arquivo_wav)
            audio_segment.export(caminho_wav, format="wav")

            duracao_segundos = audio_segment.duration_seconds

            return caminho_wav, nome_arquivo_wav, duracao_segundos
        finally:
            if os.path.exists(caminho_temp_original):
                os.remove(caminho_temp_original)

    def transcrever(self, bytes_audio: bytes, nome_original: str = "gravacao.wav") -> Dict[str, Any]:
        """
        Pipeline completo: converte o áudio para WAV, executa o reconhecimento
        de fala em pt-BR via Google Speech API e retorna um dicionário pronto
        para ser persistido pelo repositório.
        """
        try:
            caminho_wav, nome_arquivo_wav, duracao = self._converter_para_wav(bytes_audio, nome_original)

            with sr.AudioFile(caminho_wav) as fonte_audio:
                dados_audio = self.recognizer.record(fonte_audio)

            texto = self.recognizer.recognize_google(dados_audio, language="pt-BR")

            logger.info(f"Áudio transcrito com sucesso: {nome_arquivo_wav} | Duração={duracao:.2f}s")

            return {
                "nome_arquivo": nome_arquivo_wav,
                "texto_transcrito": texto,
                "idioma": "pt-BR",
                "duracao_segundos": duracao,
                "sucesso": True,
                "mensagem_erro": None,
            }

        except sr.UnknownValueError:
            mensagem = "Não foi possível compreender o áudio. Fale de forma mais clara e sem ruídos de fundo."
            logger.warning(mensagem)
            return {
                "nome_arquivo": nome_original,
                "texto_transcrito": None,
                "idioma": "pt-BR",
                "duracao_segundos": None,
                "sucesso": False,
                "mensagem_erro": mensagem,
            }

        except sr.RequestError as e:
            mensagem = f"Erro ao se conectar ao serviço de reconhecimento de fala: {e}"
            logger.error(mensagem)
            return {
                "nome_arquivo": nome_original,
                "texto_transcrito": None,
                "idioma": "pt-BR",
                "duracao_segundos": None,
                "sucesso": False,
                "mensagem_erro": mensagem,
            }

        except Exception as e:
            mensagem = f"Erro inesperado ao processar o áudio: {e}"
            logger.error(mensagem)
            return {
                "nome_arquivo": nome_original,
                "texto_transcrito": None,
                "idioma": "pt-BR",
                "duracao_segundos": None,
                "sucesso": False,
                "mensagem_erro": mensagem,
            }
