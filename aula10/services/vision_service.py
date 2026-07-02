import os
import uuid
from datetime import datetime
from typing import Tuple, Dict, Any

import cv2
import numpy as np

from config.logger import get_logger

logger = get_logger(__name__)

DIRETORIO_IMAGENS = os.path.join("assets", "images")


class VisionService:
    """
    Serviço responsável por toda a lógica de Visão Computacional:
    cálculo de nitidez, luminosidade, cor predominante, detecção de rostos
    e persistência física da imagem em disco.
    """

    def __init__(self):
        os.makedirs(DIRETORIO_IMAGENS, exist_ok=True)
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            logger.error(
                "Não foi possível carregar o classificador Haar Cascade de detecção de rostos. "
                "Verifique a instalação do opencv-python-headless."
            )

    def _calcular_nitidez(self, imagem_gray: np.ndarray) -> float:
        """
        Calcula a nitidez da imagem usando a Variância do Laplaciano.
        Quanto maior o valor, mais nítida (menos borrada) está a imagem.
        """
        laplacian = cv2.Laplacian(imagem_gray, cv2.CV_64F)
        return float(laplacian.var())

    def _calcular_luminosidade_media(self, imagem_gray: np.ndarray) -> float:
        """
        Calcula a luminosidade média da imagem (0 a 255) a partir do canal de cinza.
        """
        return float(np.mean(imagem_gray))

    def _calcular_cor_predominante(self, imagem_bgr: np.ndarray, k: int = 3) -> Tuple[int, int, int]:
        """
        Calcula a cor predominante da imagem usando K-Means clustering.
        Retorna a tupla (R, G, B) do cluster com maior número de pixels.
        """
        imagem_pequena = cv2.resize(imagem_bgr, (100, 100), interpolation=cv2.INTER_AREA)
        pixels = imagem_pequena.reshape(-1, 3).astype(np.float32)

        criterios = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, rotulos, centros = cv2.kmeans(
            pixels, k, None, criterios, 10, cv2.KMEANS_RANDOM_CENTERS
        )

        contagens = np.bincount(rotulos.flatten())
        cor_dominante_bgr = centros[np.argmax(contagens)]
        b, g, r = cor_dominante_bgr.astype(int)
        return int(r), int(g), int(b)

    def _detectar_rostos(self, imagem_gray: np.ndarray) -> int:
        """
        Detecta rostos na imagem usando o classificador Haar Cascade embutido no OpenCV.
        Retorna a quantidade de rostos detectados.
        """
        if self.face_cascade.empty():
            return 0

        rostos = self.face_cascade.detectMultiScale(
            imagem_gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )
        return len(rostos)

    def _salvar_imagem(self, imagem_bgr: np.ndarray, nome_original: str) -> Tuple[str, str]:
        """
        Salva a imagem fisicamente em assets/images/ com nome único baseado
        em timestamp + UUID, evitando colisões de nome.
        """
        extensao = os.path.splitext(nome_original)[1] or ".jpg"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        identificador = uuid.uuid4().hex[:8]
        nome_arquivo = f"analise_{timestamp}_{identificador}{extensao}"
        caminho_completo = os.path.join(DIRETORIO_IMAGENS, nome_arquivo)

        cv2.imwrite(caminho_completo, imagem_bgr)

        return nome_arquivo, caminho_completo

    def processar_imagem(self, bytes_imagem: bytes, nome_original: str = "captura.jpg") -> Dict[str, Any]:
        """
        Pipeline completo de processamento: decodifica a imagem, calcula todas
        as métricas, salva o arquivo físico e retorna um dicionário pronto
        para ser persistido pelo repositório.
        """
        array_np = np.frombuffer(bytes_imagem, np.uint8)
        imagem_bgr = cv2.imdecode(array_np, cv2.IMREAD_COLOR)

        if imagem_bgr is None:
            raise ValueError("Não foi possível decodificar a imagem recebida da webcam.")

        imagem_gray = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
        altura, largura = imagem_bgr.shape[:2]

        nitidez = self._calcular_nitidez(imagem_gray)
        luminosidade = self._calcular_luminosidade_media(imagem_gray)
        r, g, b = self._calcular_cor_predominante(imagem_bgr)
        total_rostos = self._detectar_rostos(imagem_gray)
        nome_arquivo, caminho_completo = self._salvar_imagem(imagem_bgr, nome_original)

        logger.info(
            f"Imagem processada: {nome_arquivo} | Nitidez={nitidez:.2f} | "
            f"Luminosidade={luminosidade:.2f} | Rostos={total_rostos} | "
            f"Resolução={largura}x{altura}"
        )

        return {
            "nome_arquivo": nome_arquivo,
            "caminho_imagem": caminho_completo,
            "nitidez": nitidez,
            "luminosidade_media": luminosidade,
            "cor_predominante_r": r,
            "cor_predominante_g": g,
            "cor_predominante_b": b,
            "rostos_detectados": total_rostos,
            "largura_px": largura,
            "altura_px": altura,
        }
