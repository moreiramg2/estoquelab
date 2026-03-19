import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Estoque Lab", layout="wide", page_icon="🧪")

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

    # fallback inteligente
    if "quantidade_retirada" not in df.columns:
        if "quantidade" in df.columns:
            df["quantidade_retirada"] = df["quantidade"]

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
        st.subheader("📊 Estoque por reagente")
        estoque_plot = df.groupby("nome")["quantidade"].sum().reset_index()

        fig1 = px.bar(
            estoque_plot,
            x="nome",
            y="quantidade",
            color="nome",
            title="Estoque atual"
        )

        st.plotly_chart(fig1, use_container_width=True)

        # CONSUMO
        st.subheader("📉 Consumo por reagente")

        if not hist.empty:

            hist_plot = hist.copy()
            hist_plot["nome"] = hist_plot["nome"].astype(str)
            hist_plot["data"] = pd.to_datetime(hist_plot["data"])

            consumo = hist_plot.groupby(["data","nome"])["quantidade_retirada"].sum().reset_index()

            # acumulado
            consumo["acumulado"] = consumo.groupby("nome")["quantidade_retirada"].cumsum()

            fig2 = px.line(
                consumo,
                x="data",
                y="acumulado",
                color="nome",
                markers=True,
                title="Consumo acumulado"
            )

            st.plotly_chart(fig2, use_container_width=True)

            # TOP CONSUMO
            st.subheader("🔥 Reagentes mais consumidos")

            top = hist.groupby("nome")["quantidade_retirada"].sum().sort_values(ascending=False)

            st.bar_chart(top)

            # PREVISÃO 🔥🔥🔥
            st.subheader("⏳ Previsão de término de estoque")

            previsoes = []

            for nome in df["nome"].unique():

                consumo_total = hist[hist["nome"] == nome]["quantidade_retirada"].sum()

                dias = (hist["data"].max() - hist["data"].min()).days

                if dias > 0 and consumo_total > 0:

                    consumo_medio = consumo_total / dias

                    estoque_atual = df[df["nome"] == nome]["quantidade"].sum()

                    dias_restantes = estoque_atual / consumo_medio

                    previsoes.append({
                        "Reagente": nome,
                        "Dias restantes": round(dias_restantes,1)
                    })

            if previsoes:
                df_prev = pd.DataFrame(previsoes).sort_values("Dias restantes")
                st.dataframe(df_prev, use_container_width=True)
            else:
                st.info("Sem dados suficientes para previsão")

        else:
            st.info("Sem histórico ainda")

        st.divider()

        # TABELA
        st.subheader("📋 Estoque atual")

        def highlight(row):
            if row["quantidade"] <= row["minimo"]:
                return ["background-color: #fff3cd"]*len(row)
            if pd.notnull(row["validade"]) and row["validade"] <= datetime.now() + pd.Timedelta(days=30):
                return ["background-color: #f8d7da"]*len(row)
            return [""]*len(row)

        df["nome"] = df["nome"].fillna("").astype(str)
        df["lote"] = df["lote"].fillna("").astype(str)

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
            aba_estoque.append_row([
                str(nome),
                str(lote),
                int(quantidade),
                int(minimo),
                str(status),
                str(validade)
            ])
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

                nome = str(df.loc[idx,"nome"])
                lote = str(df.loc[idx,"lote"])
                data = datetime.now().strftime("%Y-%m-%d")

                aba_historico.append_row([
                    nome,
                    lote,
                    int(qtd),
                    data
                ])

                if nova == 0:
                    aba_estoque.delete_rows(int(idx)+2)
                    st.warning("Lote removido")

                else:
                    aba_estoque.update_cell(int(idx)+2,3,int(nova))
                    st.success("Atualizado")

                st.rerun()

    else:
        st.info("Sem itens no estoque")
