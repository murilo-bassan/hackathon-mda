import time
import random
from pathlib import Path

import pandas as pd
import streamlit as st

from general_process.core.graph_builder import graph
from process_request.utilities.config import DATA_PATH
from general_process.utilities.logger_config import setup_logger

logger = setup_logger(__name__)

LOG_FILE = Path("logs/execucao.log")

@st.cache_data
def load_data():
    data = pd.read_json(DATA_PATH)
    return data.to_dict(orient="records")

tickets = load_data()

st.set_page_config(
    page_title="Processo Geral",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("# Processo Geral")
st.divider()

aba1, aba2 = st.tabs([
    "Distribuição Inteligente",
    "Teste Geral"
])

with aba1:

    selected_ticket = st.selectbox(
        "Ticket",
        tickets,
        format_func=lambda x: f"{x['id']} | {x['free_text'][:80]}"
    )

    if st.button(
        "Executar Processo Geral",
        type="primary",
        use_container_width=True
    ):

        progress = st.progress(0)

        for i in range(100):
            time.sleep(0.01)
            progress.progress(i + 1)

        response = graph.invoke({
            "ticket": selected_ticket
        })

        resultado = response.get("response", {})

        st.json(resultado)

with aba2:

    quantidade = st.slider(
        "Quantidade",
        1,
        30,
        5
    )

    if st.button(
        "Executar Teste Geral",
        use_container_width=True
    ):

        lote = random.sample(tickets, quantidade)

        resultados = []

        progress = st.progress(0)

        for idx, ticket in enumerate(lote):

            progress.progress((idx + 1) / quantidade)

            try:

                resp = graph.invoke({
                    "ticket": ticket
                })

                data = resp.get("response", {})

                resultados.append({
                    "ID": ticket["id"],
                    "Categoria": data.get("category"),
                    "Prioridade": data.get("resulting_priority"),
                    "Departamento": data.get("department")
                })

            except Exception as e:
                logger.error(e)

        st.dataframe(
            pd.DataFrame(resultados),
            use_container_width=True,
            hide_index=True
        )