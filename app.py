import streamlit as st

# =========================================================
# CONFIGURAÇÃO
# =========================================================
st.set_page_config(
    page_title="Central AGETIC",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.card {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 28px;
    background: #111111;
    transition: 0.2s ease;
    min-height: 240px;
}

.card:hover {
    border: 1px solid rgba(255,255,255,0.20);
    transform: translateY(-3px);
}

.card-title {
    font-size: 28px;
    font-weight: 700;
    margin-top: 18px;
    margin-bottom: 12px;
}

.card-description {
    color: #c5c5c5;
    font-size: 15px;
    line-height: 1.5;
    margin-bottom: 28px;
}

.material-symbols-outlined {
    font-size: 52px !important;
    color: white;
}

.card-button {
    margin-top: auto;
}

</style>

<link rel="stylesheet"
href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("# Central de Triagem AGETIC")
st.markdown("Selecione o fluxo desejado.")
st.divider()

# =========================================================
# CARDS
# =========================================================
col1, col2, col3 = st.columns(3)

# =========================================================
# PROCESSO GERAL
# =========================================================
with col1:

    with st.container(border=True):

        st.markdown("""
        <span class="material-symbols-outlined">
        alt_route
        </span>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card-title">
        Processo Geral
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card-description">
        Distribuição inteligente entre os fluxos de Requests e Incidents.
        </div>
        """, unsafe_allow_html=True)

        st.page_link(
            "pages/app_general.py",
            label="Abrir Processo Geral",
            icon=":material/arrow_forward:"
        )

# =========================================================
# REQUESTS
# =========================================================
with col2:

    with st.container(border=True):

        st.markdown("""
        <span class="material-symbols-outlined">
        request_page
        </span>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card-title">
        Processo 3.1 - Requests
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card-description">
        Triagem especializada para requisições, acessos e serviços.
        </div>
        """, unsafe_allow_html=True)

        st.page_link(
            "pages/app_requests.py",
            label="Abrir Processo Requests",
            icon=":material/arrow_forward:"
        )

# =========================================================
# INCIDENTS
# =========================================================
with col3:

    with st.container(border=True):

        st.markdown("""
        <span class="material-symbols-outlined">
        warning
        </span>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card-title">
        Processo 3.5 - Incidents
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card-description">
        Triagem especializada para incidentes críticos e operacionais.
        </div>
        """, unsafe_allow_html=True)

        st.page_link(
            "pages/app_incidents.py",
            label="Abrir Processo Incidents",
            icon=":material/arrow_forward:"
        )