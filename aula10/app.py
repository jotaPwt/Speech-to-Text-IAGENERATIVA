import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.logger import get_logger
from config.database import init_db
from controllers.analise_controller import AnaliseController
from controllers.audio_controller import AudioController

logger = get_logger(__name__)

st.set_page_config(
    page_title="Visão & Voz | Sistema Multimodal",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def inicializar_banco() -> bool:
    init_db()
    return True


@st.cache_resource
def obter_analise_controller() -> AnaliseController:
    return AnaliseController()


@st.cache_resource
def obter_audio_controller() -> AudioController:
    return AudioController()


def renderizar_cabecalho() -> None:
    st.title("🧠 Sistema Multimodal — Visão Computacional & Voz")
    st.caption(
        "Processamento de imagem via OpenCV e transcrição de áudio via SpeechRecognition, "
        "persistidos em PostgreSQL (Neon.tech)."
    )
    st.divider()


def renderizar_aba_visao(controller: AnaliseController) -> None:
    st.subheader("📷 Captura e Análise de Imagem")
    st.write(
        "Utilize sua webcam para capturar uma imagem. O sistema calculará nitidez, "
        "luminosidade, cor predominante e detectará rostos automaticamente."
    )

    imagem_capturada = st.camera_input("Capturar imagem pela webcam", key="camera_visao")

    if imagem_capturada is not None:
        if st.button("🔍 Processar e Salvar Imagem", type="primary", key="btn_processar_imagem"):
            with st.spinner("Processando imagem com OpenCV..."):
                bytes_imagem = imagem_capturada.getvalue()
                resultado = controller.processar_e_salvar(
                    bytes_imagem, imagem_capturada.name or "captura.jpg"
                )

            if resultado:
                st.success(f"Imagem processada e salva com sucesso! ID={resultado['id']}")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Nitidez (Var. Laplaciana)", f"{resultado['nitidez']:.2f}")
                col2.metric("Luminosidade Média", f"{resultado['luminosidade_media']:.2f}")
                col3.metric("Rostos Detectados", resultado["rostos_detectados"])
                col4.metric("Resolução", resultado["resolucao"])

                st.markdown(f"**Cor Predominante:** `{resultado['cor_predominante']}`")

                swatch_html = (
                    f'<div style="width:100px;height:40px;border-radius:6px;'
                    f'background:{resultado["cor_predominante"]};border:1px solid #ccc;"></div>'
                )
                st.markdown(swatch_html, unsafe_allow_html=True)

                if resultado["rostos_detectados"] == 0:
                    st.warning("Nenhum rosto foi detectado na imagem.")
                else:
                    st.info(f"{resultado['rostos_detectados']} rosto(s) detectado(s) na imagem.")
            else:
                st.error("Ocorreu um erro ao processar a imagem. Verifique os logs do sistema.")


def renderizar_aba_audio(controller: AudioController) -> None:
    st.subheader("🎙️ Captura e Transcrição de Áudio")
    st.write(
        "Grave um áudio pelo microfone. O sistema transcreverá a fala para texto "
        "em Português do Brasil."
    )

    audio_capturado = st.audio_input("Gravar áudio pelo microfone", key="audio_stt")

    if audio_capturado is not None:
        st.audio(audio_capturado)

        if st.button("📝 Transcrever e Salvar Áudio", type="primary", key="btn_processar_audio"):
            with st.spinner("Transcrevendo áudio, aguarde..."):
                bytes_audio = audio_capturado.getvalue()
                resultado = controller.processar_e_salvar(bytes_audio, "gravacao.wav")

            if resultado and resultado.get("sucesso"):
                st.success(f"Áudio transcrito e salvo com sucesso! ID={resultado['id']}")
                st.markdown("**Texto transcrito:**")
                st.info(resultado["texto_transcrito"])
                if resultado.get("duracao_segundos"):
                    st.caption(f"Duração: {resultado['duracao_segundos']:.2f} segundos")
            elif resultado:
                st.warning(f"A transcrição não teve sucesso: {resultado.get('mensagem_erro')}")
            else:
                st.error("Ocorreu um erro ao processar o áudio. Verifique os logs do sistema.")


def renderizar_aba_dashboard_visao(controller: AnaliseController) -> None:
    st.subheader("📊 Histórico de Análises de Imagem")

    historico = controller.listar_historico()

    if not historico:
        st.info("Nenhuma análise de imagem registrada até o momento.")
        return

    df = pd.DataFrame(historico)

    col_esq, col_dir = st.columns([2, 1])

    with col_esq:
        st.markdown("### Registros")
        st.dataframe(
            df[
                [
                    "id",
                    "nome_arquivo",
                    "nitidez",
                    "luminosidade_media",
                    "cor_predominante",
                    "rostos_detectados",
                    "resolucao",
                    "criado_em",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with col_dir:
        st.markdown("### Ações")
        ids_disponiveis = df["id"].tolist()
        id_selecionado = st.selectbox("Selecionar ID do registro", ids_disponiveis, key="select_id_visao")

        registro_selecionado = df[df["id"] == id_selecionado].iloc[0]
        caminho_imagem = controller.obter_caminho_imagem(int(id_selecionado))

        if caminho_imagem and os.path.exists(caminho_imagem):
            st.image(caminho_imagem, caption=registro_selecionado["nome_arquivo"], use_container_width=True)

            with open(caminho_imagem, "rb") as arquivo_imagem:
                st.download_button(
                    label="⬇️ Baixar Imagem",
                    data=arquivo_imagem.read(),
                    file_name=registro_selecionado["nome_arquivo"],
                    mime="image/jpeg",
                    key="download_imagem",
                    use_container_width=True,
                )
        else:
            st.warning("Arquivo de imagem não encontrado no disco.")

        if st.button("🗑️ Excluir Registro", type="secondary", key="btn_excluir_visao", use_container_width=True):
            sucesso = controller.excluir_analise(int(id_selecionado))
            if sucesso:
                st.success("Registro excluído com sucesso!")
                st.rerun()
            else:
                st.error("Não foi possível excluir o registro.")

    st.markdown("### 📈 Evolução das Métricas")
    df_grafico = (
        df.sort_values("criado_em")[["criado_em", "nitidez", "luminosidade_media"]]
        .set_index("criado_em")
    )
    st.line_chart(df_grafico)


def renderizar_aba_dashboard_audio(controller: AudioController) -> None:
    st.subheader("📊 Histórico de Transcrições")

    historico = controller.listar_historico()

    if not historico:
        st.info("Nenhuma transcrição registrada até o momento.")
        return

    df = pd.DataFrame(historico)

    st.dataframe(
        df[["id", "nome_arquivo", "texto_transcrito", "duracao_segundos", "sucesso", "criado_em"]],
        use_container_width=True,
        hide_index=True,
    )

    ids_disponiveis = df["id"].tolist()
    id_selecionado = st.selectbox(
        "Selecionar ID da transcrição para excluir", ids_disponiveis, key="select_id_audio"
    )

    if st.button("🗑️ Excluir Transcrição", type="secondary", key="btn_excluir_audio"):
        sucesso = controller.excluir_transcricao(int(id_selecionado))
        if sucesso:
            st.success("Transcrição excluída com sucesso!")
            st.rerun()
        else:
            st.error("Não foi possível excluir a transcrição.")

    if "duracao_segundos" in df.columns and df["duracao_segundos"].notna().any():
        st.markdown("### 📈 Duração das Gravações")
        df_grafico = (
            df.sort_values("criado_em")[["criado_em", "duracao_segundos"]]
            .dropna()
            .set_index("criado_em")
        )
        st.line_chart(df_grafico)


def main() -> None:
    try:
        inicializar_banco()
    except Exception as e:
        st.error(
            f"Erro ao conectar ao banco de dados. Verifique a variável de ambiente "
            f"DATABASE_URL. Detalhes: {e}"
        )
        st.stop()

    renderizar_cabecalho()

    analise_controller = obter_analise_controller()
    audio_controller = obter_audio_controller()

    with st.sidebar:
        st.header("⚙️ Navegação")
        st.markdown(
            "Sistema desenvolvido com **Streamlit**, **OpenCV**, **SpeechRecognition** "
            "e **PostgreSQL (Neon.tech)**."
        )
        st.divider()
        st.markdown("**Módulos disponíveis:**")
        st.markdown("- 📷 Visão Computacional\n- 🎙️ Transcrição de Áudio\n- 📊 Dashboards e Histórico")

    aba_visao, aba_audio, aba_dashboard_visao, aba_dashboard_audio = st.tabs(
        [
            "📷 Captura de Imagem",
            "🎙️ Captura de Áudio",
            "📊 Dashboard - Imagens",
            "📊 Dashboard - Áudio",
        ]
    )

    with aba_visao:
        renderizar_aba_visao(analise_controller)

    with aba_audio:
        renderizar_aba_audio(audio_controller)

    with aba_dashboard_visao:
        renderizar_aba_dashboard_visao(analise_controller)

    with aba_dashboard_audio:
        renderizar_aba_dashboard_audio(audio_controller)


if __name__ == "__main__":
    main()
