import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Estoque Lab Pro", layout="wide", page_icon="🧪")

# 🔥 ESTILO PROFISSIONAL
st.markdown("""
<style>
.main {
    background-color: #f5f7fa;
}
.block-container {
    padding-top: 2rem;
}
.stMetric {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

SHEET_ID = "1tmsV_1h78N3NINJZ6yj6OUGOVxbgeQQikadIzTEKyGk"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

aba_estoque = client.open_by_key(SHEET_ID).worksheet("estoque")
aba_historico = client.open_by_key(SHEET_ID).worksheet("historico")

# =========================
# LOGIN
# =========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user == "admin" and senha == "123":
            st.session_state.logado = True
            st.session_state.usuario = user
            st.rerun()
        else:
            st.error("Login inválido")

    st.stop()

# =========================
# MENU
# =========================
menu = st.sidebar.selectbox(
    "📌 Menu",
    ["Dashboard", "Cadastro", "Retirada", "Relatórios"]
)

st.sidebar.success(f"Logado como: {st.session_state.usuario}")

# =========================
# LOAD DADOS
# =========================
def load_data():
    df = pd.DataFrame(aba_estoque.get_all_records())
    if df.empty:
        return pd.DataFrame(columns=["nome","lote","quantidade","minimo","status_validacao","validade"])

    df.columns = df.columns.str.strip().str.lower()
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    df["minimo"] = pd.to_numeric(df["minimo"], errors="coerce")
    df["validade"] = pd.to_datetime(df["validade"], errors="coerce")
    return df


def load_hist():
    df = pd.DataFrame(aba_historico.get_all_records())
    if df.empty:
        return pd.DataFrame(columns=["nome","lote","quantidade_retirada","data","usuario"])

    df.columns = df.columns.str.strip().str.lower()

    if "quantidade_retirada" not in df.columns:
        df["quantidade_retirada"] = df.get("quantidade", 0)

    df["quantidade_retirada"] = pd.to_numeric(df["quantidade_retirada"], errors="coerce")
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    return df


df = load_data()
hist = load_hist()

if not df.empty:
    df = df[df["quantidade"] > 0]

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    st.title("📊 Dashboard")

    if not df.empty:

        col1, col2, col3 = st.columns(3)

        col1.metric("📦 Lotes", len(df))
        col2.metric("⚠️ Estoque baixo", len(df[df["quantidade"] <= df["minimo"]]))
        col3.metric("📅 Vencendo", len(df[df["validade"] <= datetime.now() + pd.Timedelta(days=30)]))

        st.divider()

        # ALERTAS
        baixo = df[df["quantidade"] <= df["minimo"]]
        vencendo = df[df["validade"] <= datetime.now() + pd.Timedelta(days=30)]

        if not baixo.empty:
            st.warning("Itens com estoque baixo")

        if not vencendo.empty:
            st.error("Itens próximos do vencimento")

        st.divider()

        # ESTOQUE
        estoque_plot = df.groupby("nome")["quantidade"].sum().reset_index()

        fig1 = px.bar(estoque_plot, x="nome", y="quantidade", color="nome")
        st.plotly_chart(fig1, use_container_width=True)

        # CONSUMO
        if not hist.empty:

            hist["nome"] = hist["nome"].astype(str)
            consumo = hist.groupby(["data","nome"])["quantidade_retirada"].sum().reset_index()

            consumo["acumulado"] = consumo.groupby("nome")["quantidade_retirada"].cumsum()

            fig2 = px.line(
                consumo,
                x="data",
                y="acumulado",
                color="nome",
                markers=True
            )

            st.plotly_chart(fig2, use_container_width=True)

            # PREVISÃO
            st.subheader("⏳ Previsão de estoque")

            previsoes = []

            for nome in df["nome"].unique():
                consumo_total = hist[hist["nome"] == nome]["quantidade_retirada"].sum()
                dias = (hist["data"].max() - hist["data"].min()).days

                if dias > 0 and consumo_total > 0:
                    media = consumo_total / dias
                    estoque = df[df["nome"] == nome]["quantidade"].sum()
                    dias_rest = estoque / media

                    previsoes.append([nome, round(dias_rest,1)])

            if previsoes:
                st.dataframe(pd.DataFrame(previsoes, columns=["Reagente","Dias restantes"]))

    else:
        st.info("Sem dados")

# =========================
# CADASTRO
# =========================
elif menu == "Cadastro":

    st.title("➕ Cadastro")

    with st.form("add"):
        nome = st.text_input("Nome")
        lote = st.text_input("Lote")
        qtd = st.number_input("Quantidade", min_value=1)
        minimo = st.number_input("Mínimo", min_value=1)
        validade = st.date_input("Validade")
        status = st.selectbox("Status", ["Aprovado","Pendente","Reprovado"])

        if st.form_submit_button("Salvar"):
            aba_estoque.append_row([
                nome, lote, int(qtd), int(minimo), status, str(validade)
            ])
            st.success("Adicionado!")
            st.rerun()

# =========================
# RETIRADA
# =========================
elif menu == "Retirada":

    st.title("➖ Retirada")

    if not df.empty:

        df["nome"] = df["nome"].astype(str)
        df["lote"] = df["lote"].astype(str)
        df["id"] = df["nome"] + " | " + df["lote"]

        item = st.selectbox("Item", df["id"])
        qtd = st.number_input("Quantidade", min_value=1)

        if st.button("Retirar"):

            idx = df[df["id"] == item].index[0]
            atual = int(df.loc[idx,"quantidade"])

            if qtd > atual:
                st.error("Quantidade inválida")

            else:
                nova = atual - qtd

                nome = str(df.loc[idx,"nome"])
                lote = str(df.loc[idx,"lote"])

                aba_historico.append_row([
                    nome,
                    lote,
                    int(qtd),
                    datetime.now().strftime("%Y-%m-%d"),
                    st.session_state.usuario
                ])

                if nova == 0:
                    aba_estoque.delete_rows(int(idx)+2)
                else:
                    aba_estoque.update_cell(int(idx)+2,3,int(nova))

                st.success("Retirada registrada")
                st.rerun()

# =========================
# RELATÓRIOS
# =========================
elif menu == "Relatórios":

    st.title("📄 Relatórios")

    if not hist.empty:

        st.dataframe(hist, use_container_width=True)

        csv = hist.to_csv(index=False)

        st.download_button(
            "📥 Baixar CSV",
            csv,
            "relatorio.csv",
            "text/csv"
        )

    else:
        st.info("Sem histórico")