import time
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from general_process.core.graph_builder import graph
from process_request.utilities.config import DATA_PATH
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

LOG_FILE = Path("logs/execucao.log")


# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Processo 3.1 - Requests",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# DATASET
# =========================================================
@st.cache_data
def load_data():
    data = pd.read_json(DATA_PATH)
    return data.to_dict(orient="records")


tickets = load_data()


# =========================================================
# LOGS
# =========================================================
def get_logs():
    if not LOG_FILE.exists():
        return "Aguardando execução..."

    logs = LOG_FILE.read_text(encoding="utf-8").splitlines()
    logs.reverse()

    return "\n".join(logs[:200])


def limpar_logs():
    if LOG_FILE.exists():
        LOG_FILE.write_text("", encoding="utf-8")

    st.rerun()


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("### Terminal")

    if st.button("Limpar Logs", use_container_width=True):
        limpar_logs()

    with st.container(height=500):
        st.code(get_logs(), language="bash")


# =========================================================
# HEADER
# =========================================================
st.title("Processo 3.1 - Requests")
st.caption("Fluxo especializado para requisições de serviço.")
st.divider()


# =========================================================
# TABS
# =========================================================
aba1, aba2 = st.tabs([
    "Análise Individual",
    "Teste em Lote"
])


# =========================================================
# ABA 1
# =========================================================
with aba1:

    def format_ticket_label(t):
        texto = t.get("free_text", "")
        preview = texto[:80] + "..." if len(texto) > 80 else texto
        return f"{t['id']} | {preview}"

    ticket_options = {format_ticket_label(t): t for t in tickets}

    with st.container(border=True):

        col1, col2 = st.columns([4, 1])

        with col1:
            selected_label = st.selectbox(
                "Chamado",
                list(ticket_options.keys()),
                label_visibility="collapsed"
            )

        with col2:
            usar_ticket_real = st.toggle(
                "Dataset",
                value=True
            )

        selected_ticket = ticket_options[selected_label]

        texto_chamado = st.text_area(
            "Descrição",
            value=selected_ticket["free_text"] if usar_ticket_real else "",
            height=140
        )

    st.write("")

    if "executando_request" not in st.session_state:
        st.session_state.executando_request = False

    if not st.session_state.executando_request:

        if st.button(
            "Executar Triagem",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.executando_request = True
            st.rerun()

    else:

        colA, colB = st.columns([4, 1])

        with colA:
            st.button(
                "Processando...",
                disabled=True,
                use_container_width=True
            )

        with colB:
            if st.button(
                "Cancelar",
                use_container_width=True
            ):
                st.session_state.executando_request = False
                st.rerun()

        try:

            ticket_payload = selected_ticket if usar_ticket_real else {
                "id": "REQ-MANUAL",
                "timestamp": datetime.now().isoformat(),
                "channel": "Web",
                "requester_profile": "Usuário",
                "free_text": texto_chamado
            }

            progress = st.progress(0)

            progress.progress(15)

            with st.status("Executando fluxo de Requests...", expanded=True):

                response = graph.invoke({
                    "ticket": ticket_payload
                })

                progress.progress(60)

                time.sleep(0.4)

                progress.progress(100)

            resultado = response.get("response", {})

            prioridade = resultado.get("resulting_priority", "N/A")
            categoria = resultado.get("category", "N/A")
            departamento = resultado.get("department", "N/A")

            justificativa = resultado.get(
                "priority_justification",
                "Sem justificativa"
            )

            resposta = resultado.get(
                "response_draft",
                "Sem resposta"
            )

            st.divider()

            col1, col2, col3 = st.columns(3)

            col1.metric("Prioridade", prioridade)
            col2.metric("Categoria", categoria)
            col3.metric("Departamento", departamento)

            st.write("")

            c1, c2 = st.columns(2)

            with c1:
                with st.container(border=True):
                    st.markdown("#### Comparação")
                    st.info(justificativa)

            with c2:
                with st.container(border=True):
                    st.markdown("#### Resposta")
                    st.success(resposta)

            with st.expander("JSON Completo"):
                st.json(resultado)

        except Exception as e:
            logger.exception(e)
            st.error(str(e))

        st.session_state.executando_request = False


# =========================================================
# ABA 2 - LOTE
# =========================================================
with aba2:

    st.subheader("Teste Aleatório em Lote")

    quantidade = st.slider(
        "Quantidade",
        min_value=1,
        max_value=20,
        value=5
    )

    if st.button(
        "Executar Lote",
        use_container_width=True
    ):

        lote = random.sample(tickets, quantidade)

        resultados = []

        progresso = st.progress(0)

        for idx, ticket in enumerate(lote):

            progresso.progress((idx + 1) / quantidade)

            try:

                response = graph.invoke({
                    "ticket": ticket
                })

                resultado = response.get("response", {})

                resultados.append({
                    "ID": ticket["id"],
                    "Categoria IA": resultado.get("category"),
                    "Prioridade IA": resultado.get("resulting_priority"),
                    "Departamento IA": resultado.get("department")
                })

            except Exception as e:
                logger.error(e)

        st.success("Lote concluído.")

        st.dataframe(
            pd.DataFrame(resultados),
            use_container_width=True,
            hide_index=True
        )