import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Estoque Lab",
    layout="wide",
    page_icon="🧪"
)

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
# LOAD DADOS
# =========================
def load_data():
    data = aba_estoque.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["nome","lote","quantidade","minimo","status_validacao","validade"])

    df.columns = df.columns.str.strip().str.lower()
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    df["minimo"] = pd.to_numeric(df["minimo"], errors="coerce")
    df["validade"] = pd.to_datetime(df["validade"], errors="coerce")

    return df

def load_historico():
    data = aba_historico.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["nome","lote","quantidade_retirada","data"])

    df.columns = df.columns.str.strip().str.lower()
    df["quantidade_retirada"] = pd.to_numeric(df["quantidade_retirada"], errors="coerce")
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    return df

df = load_data()
hist = load_historico()

if not df.empty:
    df = df[df["quantidade"] > 0]

# =========================
# UI
# =========================
st.title("🧪 Sistema de Estoque Inteligente")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Cadastro", "➖ Retirada"])

# =========================
# DASHBOARD
# =========================
with tab1:

    if not df.empty:

        # METRICAS
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Lotes", len(df))
        col2.metric("⚠️ Estoque baixo", len(df[df["quantidade"] <= df["minimo"]]))
        col3.metric("📅 Vencendo", len(df[df["validade"] <= datetime.now() + pd.Timedelta(days=30)]))

        st.divider()

        # ALERTAS
        st.subheader("🚨 Alertas")

        estoque_baixo = df[df["quantidade"] <= df["minimo"]]
        vencendo = df[df["validade"] <= datetime.now() + pd.Timedelta(days=30)]

        if not estoque_baixo.empty:
            st.warning(f"{len(estoque_baixo)} itens com estoque baixo")

        if not vencendo.empty:
            st.error(f"{len(vencendo)} itens próximos do vencimento")

        if estoque_baixo.empty and vencendo.empty:
            st.success("Tudo OK!")

        st.divider()

        # GRAFICO ESTOQUE
        st.subheader("📊 Estoque atual por reagente")
        st.bar_chart(df.groupby("nome")["quantidade"].sum())

        # GRAFICO CONSUMO
        st.subheader("📉 Consumo ao longo do tempo")

        if not hist.empty:
            consumo = hist.groupby("data")["quantidade_retirada"].sum()
            st.line_chart(consumo)
        else:
            st.info("Sem dados de consumo ainda")

        st.divider()

        # TABELA
        st.subheader("📋 Estoque")

        def highlight(row):
            if row["quantidade"] <= row["minimo"]:
                return ["background-color: #fff3cd"]*len(row)
            if row["validade"] <= datetime.now() + pd.Timedelta(days=30):
                return ["background-color: #f8d7da"]*len(row)
            return [""]*len(row)

        df["id_item"] = df["nome"] + " | Lote: " + df["lote"]

        st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

# =========================
# CADASTRO
# =========================
with tab2:

    with st.form("add"):
        nome = st.text_input("Nome")
        lote = st.text_input("Lote")
        quantidade = st.number_input("Quantidade", min_value=1)
        minimo = st.number_input("Estoque mínimo", min_value=1)
        validade = st.date_input("Validade")
        status = st.selectbox("Status", ["Aprovado","Pendente","Reprovado"])

        if st.form_submit_button("Adicionar"):
            aba_estoque.append_row([nome,lote,int(quantidade),int(minimo),status,str(validade)])
            st.success("Adicionado!")
            st.rerun()

# =========================
# RETIRADA
# =========================
with tab3:

    if not df.empty:

        item = st.selectbox("Item", df["id_item"])
        qtd = st.number_input("Quantidade", min_value=1)

        if st.button("Retirar"):

            idx = df[df["id_item"] == item].index[0]
            atual = int(df.loc[idx,"quantidade"])

            if qtd > atual:
                st.error("Quantidade inválida")

            else:
                nova = atual - qtd

                # REGISTRA HISTORICO 🔥
                aba_historico.append_row([
                    df.loc[idx,"nome"],
                    df.loc[idx,"lote"],
                    int(qtd),
                    str(datetime.now())
                ])

                if nova == 0:
                    aba_estoque.delete_rows(int(idx)+2)
                    st.warning("Lote removido")

                else:
                    aba_estoque.update_cell(int(idx)+2,3,int(nova))
                    st.success("Atualizado")

                st.rerun()