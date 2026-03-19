import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Estoque Lab Pro", layout="wide")

# 🌙 DARK MODE
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}
section[data-testid="stSidebar"] {
    background-color: #111827;
}
.stMetric {
    background-color: #1f2937;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE SAFE
# =========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "tipo" not in st.session_state:
    st.session_state.tipo = None

# =========================
# GOOGLE SHEETS
# =========================
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
aba_usuarios = client.open_by_key(SHEET_ID).worksheet("usuarios")

# =========================
# LOAD USERS
# =========================
def load_users():
    df = pd.DataFrame(aba_usuarios.get_all_records())
    if df.empty:
        return pd.DataFrame(columns=["usuario","senha","tipo"])
    df.columns = df.columns.str.strip().str.lower()
    return df

usuarios_df = load_users()

# =========================
# LOGIN
# =========================
if not st.session_state.logado:

    st.title("🔐 Login")

    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        user_row = usuarios_df[
            (usuarios_df["usuario"] == user) &
            (usuarios_df["senha"] == senha)
        ]

        if not user_row.empty:
            st.session_state.logado = True
            st.session_state.usuario = user
            st.session_state.tipo = user_row.iloc[0]["tipo"]
            st.rerun()
        else:
            st.error("Login inválido")

    st.stop()

# =========================
# SIDEBAR
# =========================
menu = st.sidebar.selectbox(
    "📌 Menu",
    ["Dashboard", "Cadastro", "Retirada", "Relatórios"]
)

usuario = st.session_state.get("usuario", "desconhecido")
tipo_usuario = st.session_state.get("tipo", "desconhecido")

st.sidebar.markdown(f"👤 **{usuario}**")
st.sidebar.markdown(f"🔑 {tipo_usuario}")

# =========================
# LOAD DATA
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

        col1.metric("Lotes", len(df))
        col2.metric("Estoque baixo", len(df[df["quantidade"] <= df["minimo"]]))
        col3.metric("Vencendo", len(df[df["validade"] <= datetime.now() + pd.Timedelta(days=30)]))

        fig1 = px.bar(
            df.groupby("nome")["quantidade"].sum().reset_index(),
            x="nome", y="quantidade", color="nome"
        )
        st.plotly_chart(fig1, use_container_width=True)

        if not hist.empty:
            consumo = hist.groupby(["data","nome"])["quantidade_retirada"].sum().reset_index()
            consumo["acumulado"] = consumo.groupby("nome")["quantidade_retirada"].cumsum()

            fig2 = px.line(consumo, x="data", y="acumulado", color="nome")
            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("Sem dados")

# =========================
# CADASTRO (ADMIN)
# =========================
elif menu == "Cadastro":

    if st.session_state.tipo != "admin":
        st.warning("Acesso restrito")
        st.stop()

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

        df["id"] = df["nome"].astype(str) + " | " + df["lote"].astype(str)

        item = st.selectbox("Item", df["id"])
        qtd = st.number_input("Quantidade", min_value=1)

        if st.button("Retirar"):

            idx = df[df["id"] == item].index[0]
            atual = int(df.loc[idx,"quantidade"])

            if qtd > atual:
                st.error("Quantidade inválida")

            else:
                nova = atual - qtd

                aba_historico.append_row([
                    str(df.loc[idx,"nome"]),
                    str(df.loc[idx,"lote"]),
                    int(qtd),
                    datetime.now().strftime("%Y-%m-%d"),
                    usuario
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

        st.download_button("📥 Baixar CSV", csv, "relatorio.csv")

    else:
        st.info("Sem dados")