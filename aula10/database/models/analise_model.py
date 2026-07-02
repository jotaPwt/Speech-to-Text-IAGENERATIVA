from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func

from config.database import Base


class Analise(Base):
    """
    Representa uma análise de imagem capturada pela webcam,
    contendo as métricas calculadas pelo módulo de Visão Computacional.
    """

    __tablename__ = "analises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_arquivo = Column(String(255), nullable=False)
    caminho_imagem = Column(String(500), nullable=False)
    nitidez = Column(Float, nullable=False)
    luminosidade_media = Column(Float, nullable=False)
    cor_predominante_r = Column(Integer, nullable=False)
    cor_predominante_g = Column(Integer, nullable=False)
    cor_predominante_b = Column(Integer, nullable=False)
    rostos_detectados = Column(Integer, nullable=False, default=0)
    largura_px = Column(Integer, nullable=False)
    altura_px = Column(Integer, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome_arquivo": self.nome_arquivo,
            "caminho_imagem": self.caminho_imagem,
            "nitidez": round(self.nitidez, 2),
            "luminosidade_media": round(self.luminosidade_media, 2),
            "cor_predominante": f"rgb({self.cor_predominante_r}, {self.cor_predominante_g}, {self.cor_predominante_b})",
            "cor_predominante_r": self.cor_predominante_r,
            "cor_predominante_g": self.cor_predominante_g,
            "cor_predominante_b": self.cor_predominante_b,
            "rostos_detectados": self.rostos_detectados,
            "resolucao": f"{self.largura_px}x{self.altura_px}",
            "largura_px": self.largura_px,
            "altura_px": self.altura_px,
            "criado_em": self.criado_em,
        }


class Transcricao(Base):
    """
    Representa uma transcrição de áudio para texto gerada pelo
    módulo de Speech-to-Text (STT).
    """

    __tablename__ = "transcricoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_arquivo = Column(String(255), nullable=False)
    texto_transcrito = Column(Text, nullable=True)
    idioma = Column(String(10), nullable=False, default="pt-BR")
    duracao_segundos = Column(Float, nullable=True)
    sucesso = Column(Boolean, nullable=False, default=True)
    mensagem_erro = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome_arquivo": self.nome_arquivo,
            "texto_transcrito": self.texto_transcrito,
            "idioma": self.idioma,
            "duracao_segundos": round(self.duracao_segundos, 2) if self.duracao_segundos is not None else None,
            "sucesso": self.sucesso,
            "mensagem_erro": self.mensagem_erro,
            "criado_em": self.criado_em,
        }
