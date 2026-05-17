import sys
from pathlib import Path

# =========================================================
# AJUSTE DE PATH DO PROJETO
# =========================================================
ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import time
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from process_incident.core.subgraph_incident_builder import build_incident_subgraph
from process_request.utilities.config import DATA_PATH
from general_process.utilities.logger_config import setup_logger

graph = build_incident_subgraph()

logger = setup_logger(__name__)

# =========================================================
# LOGGER
# =========================================================
logger = setup_logger(__name__)

LOG_FILE = ROOT_DIR / "logs" / "execucao.log"

# =========================================================
# CARREGAMENTO DOS DADOS
# =========================================================
@st.cache_data
def load_data():
    data = pd.read_json(DATA_PATH)
    return data.to_dict(orient="records")


tickets = load_data()

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Processo Incidents",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# ESTILO
# =========================================================
st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.stTextArea textarea {
    font-size: 15px !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def get_logs():
    if not LOG_FILE.exists():
        return "Aguardando execução..."

    logs = LOG_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    logs.reverse()

    return "\n".join(logs)


def limpar_logs():
    if LOG_FILE.exists():
        LOG_FILE.write_text("", encoding="utf-8")

    st.rerun()


def format_ticket_label(ticket):
    texto = ticket.get("free_text", "")

    preview = (
        texto[:80] + "..."
        if len(texto) > 80
        else texto
    )

    return f"{ticket['id']} | {preview}"


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.markdown("### Terminal de Execução")

    if st.button(
        "Limpar Logs",
        use_container_width=True
    ):
        limpar_logs()

    with st.container(height=450):
        st.code(
            get_logs(),
            language="bash"
        )

# =========================================================
# HEADER
# =========================================================
st.markdown("# Processo 3.5 - Incidents")

st.markdown("""
Pipeline especializado para tratamento de incidentes críticos,
falhas operacionais e indisponibilidades.
""")

st.divider()

# =========================================================
# ABAS
# =========================================================
aba1, aba2 = st.tabs([
    "Análise Individual",
    "Teste em Lote"
])

# =========================================================
# ABA 1
# =========================================================
with aba1:

    ticket_options = {
        format_ticket_label(t): t
        for t in tickets
    }

    with st.container(border=True):

        col_sel, col_tog = st.columns(
            [4, 1],
            vertical_alignment="center"
        )

        with col_sel:

            selected_label = st.selectbox(
                "Selecione um chamado",
                list(ticket_options.keys()),
                label_visibility="collapsed"
            )

        with col_tog:

            usar_ticket_real = st.toggle(
                "Dataset",
                value=True
            )

        selected_ticket = ticket_options[selected_label]

        texto_chamado = st.text_area(
            "Descrição do incidente",
            value=selected_ticket["free_text"]
            if usar_ticket_real
            else "",
            height=140
        )

    st.write("")

    # =====================================================
    # CONTROLE EXECUÇÃO
    # =====================================================
    if "executando_incident" not in st.session_state:
        st.session_state.executando_incident = False

    if not st.session_state.executando_incident:

        if st.button(
            "Executar Triagem de Incident",
            type="primary",
            use_container_width=True
        ):

            st.session_state.executando_incident = True
            st.rerun()

    else:

        col_exec, col_cancel = st.columns([3, 1])

        with col_exec:

            st.button(
                "Processando incidente...",
                disabled=True,
                use_container_width=True
            )

        with col_cancel:

            if st.button(
                "Cancelar",
                use_container_width=True
            ):

                st.session_state.executando_incident = False
                st.rerun()

        try:

            progress_bar = st.progress(0)

            for i in range(100):

                time.sleep(0.01)

                progress_bar.progress(i + 1)

            logger.info(
                "Processamento de incident iniciado"
            )

            ticket_payload = (
                selected_ticket
                if usar_ticket_real
                else {
                    "id": "INC-MANUAL-001",
                    "timestamp": datetime.now().isoformat(),
                    "channel": "Web",
                    "requester_profile": "Usuário",
                    "free_text": texto_chamado
                }
            )

            response = graph.invoke({
                "ticket": ticket_payload
            })

            resultado = response.get("response", {})

            prioridade = resultado.get(
                "resulting_priority",
                "N/A"
            )

            urgencia = resultado.get(
                "urgency",
                "N/A"
            )

            impacto = resultado.get(
                "impact",
                "N/A"
            )

            categoria = resultado.get(
                "category",
                "N/A"
            )

            departamento = resultado.get(
                "department",
                "N/A"
            )

            st.divider()

            st.subheader("Resultado da Análise")

            if prioridade in [4, 5]:

                st.error(
                    "Incidente crítico detectado."
                )

            elif prioridade == 3:

                st.warning(
                    "Incidente de alta prioridade."
                )

            else:

                st.success(
                    "Incidente processado com sucesso."
                )

            col1, col2, col3, col4, col5 = st.columns(5)

            col1.metric(
                "Prioridade",
                prioridade
            )

            col2.metric(
                "Urgência",
                urgencia
            )

            col3.metric(
                "Impacto",
                impacto
            )

            col4.metric(
                "Categoria",
                categoria
            )

            col5.metric(
                "Departamento",
                departamento
            )

            st.write("")

            st.markdown("### Justificativas")

            justificativas = [
                (
                    "Categoria",
                    resultado.get(
                        "category_justification"
                    )
                ),
                (
                    "Prioridade",
                    resultado.get(
                        "priority_justification"
                    )
                ),
                (
                    "Departamento",
                    resultado.get(
                        "department_justification"
                    )
                ),
                (
                    "Urgência",
                    resultado.get(
                        "urgency_justification"
                    )
                ),
                (
                    "Impacto",
                    resultado.get(
                        "impact_justification"
                    )
                ),
            ]

            for titulo, valor in justificativas:

                if valor:

                    with st.container(border=True):

                        st.markdown(
                            f"#### {titulo}"
                        )

                        st.write(valor)

            with st.expander(
                "Visualizar JSON Completo"
            ):

                st.json(resultado)

        except Exception as e:

            logger.exception(
                f"Erro no processamento: {e}"
            )

            st.error(
                f"Falha ao executar: {e}"
            )

        st.session_state.executando_incident = False

# =========================================================
# ABA 2 - TESTE EM LOTE
# =========================================================
with aba2:

    st.subheader(
        "Teste de Estresse - Incidents"
    )

    st.write("""
    Execute diversos incidents aleatórios
    para validar o comportamento do pipeline.
    """)

    quantidade = st.slider(
        "Quantidade de incidents",
        min_value=1,
        max_value=30,
        value=5
    )

    if st.button(
        "Executar Lote de Incidents",
        use_container_width=True
    ):

        lote = random.sample(
            tickets,
            quantidade
        )

        resultados = []

        progress = st.progress(0)

        for idx, ticket in enumerate(lote):

            progress.progress(
                (idx + 1) / quantidade
            )

            try:

                response = graph.invoke({
                    "ticket": ticket
                })

                data = response.get(
                    "response",
                    {}
                )

                resultados.append({
                    "ID": ticket["id"],
                    "Categoria": data.get(
                        "category"
                    ),
                    "Prioridade": data.get(
                        "resulting_priority"
                    ),
                    "Departamento": data.get(
                        "department"
                    )
                })

            except Exception as e:

                logger.error(
                    f"Erro no lote: {e}"
                )

        st.divider()

        st.dataframe(
            pd.DataFrame(resultados),
            use_container_width=True,
            hide_index=True
        )

# =========================================================
# LOGS COMPLETOS
# =========================================================
st.write("")
st.write("")

with st.expander(
    "Visualizar Logs em Tela Cheia"
):

    with st.container(height=600):

        st.code(
            get_logs(),
            language="bash"
        )