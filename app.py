import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG DA PÁGINA
# =========================
st.set_page_config(
    page_title="Estoque Lab",
    layout="wide",
    page_icon="🧪"
)

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
sheet = client.open_by_key(SHEET_ID).sheet1

# =========================
# FUNÇÃO DE DADOS
# =========================
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["nome", "lote", "quantidade", "status_validacao"])

    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()

# Remove itens zerados
if not df.empty:
    df = df[df["quantidade"] > 0]

# =========================
# TÍTULO
# =========================
st.title("🧪 Sistema de Controle de Estoque")

# =========================
# ABAS
# =========================
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Cadastro", "➖ Retirada"])

# =========================
# DASHBOARD
# =========================
with tab1:

    if not df.empty:

        # ===== METRICAS =====
        col1, col2, col3 = st.columns(3)

        total = len(df)
        aprovados = len(df[df["status_validacao"] == "Aprovado"])
        reprovados = len(df[df["status_validacao"] == "Reprovado"])

        col1.metric("📦 Total de lotes", total)
        col2.metric("✅ Aprovados", aprovados)
        col3.metric("❌ Reprovados", reprovados)

        st.divider()

        # ===== GRAFICOS =====
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Quantidade por reagente")
            grafico_qtd = df.groupby("nome")["quantidade"].sum()
            st.bar_chart(grafico_qtd)

        with col2:
            st.subheader("📊 Status dos reagentes")
            grafico_status = df["status_validacao"].value_counts()
            st.bar_chart(grafico_status)

        st.divider()

        # ===== TABELA =====
        st.subheader("📋 Estoque atual")

        def highlight_status(val):
            if val == "Reprovado":
                return "color: red; font-weight: bold"
            elif val == "Aprovado":
                return "color: green; font-weight: bold"
            elif val == "Pendente":
                return "color: orange; font-weight: bold"
            return ""

        df["id_item"] = df["nome"].astype(str) + " | Lote: " + df["lote"].astype(str)

        st.dataframe(
            df.style.applymap(highlight_status, subset=["status_validacao"]),
            use_container_width=True
        )

    else:
        st.info("Nenhum item cadastrado.")

# =========================
# CADASTRO
# =========================
with tab2:

    st.subheader("➕ Adicionar reagente")

    with st.form("form_add"):
        nome = st.text_input("Nome do reagente")
        lote = st.text_input("Lote")
        quantidade = st.number_input("Quantidade", min_value=1)
        status_validacao = st.selectbox(
            "Status",
            ["Aprovado", "Pendente", "Reprovado"]
        )

        submitted = st.form_submit_button("Adicionar")

        if submitted:
            sheet.append_row([
                nome,
                lote,
                int(quantidade),
                status_validacao
            ])
            st.success("✅ Adicionado com sucesso!")
            st.rerun()

# =========================
# RETIRADA
# =========================
with tab3:

    st.subheader("➖ Retirar reagente")

    if not df.empty:

        item = st.selectbox("Selecione", df["id_item"])

        qtd = st.number_input("Quantidade a retirar", min_value=1)

        if st.button("Retirar"):

            idx = df[df["id_item"] == item].index[0]
            quantidade_atual = int(df.loc[idx, "quantidade"])

            if qtd > quantidade_atual:
                st.error("❌ Quantidade maior que o estoque!")

            else:
                nova_qtd = quantidade_atual - qtd

                if nova_qtd == 0:
                    sheet.delete_rows(int(idx) + 2)
                    st.warning("🗑️ Lote removido (zerado)")

                else:
                    sheet.update_cell(int(idx) + 2, 3, int(nova_qtd))
                    st.success("✅ Atualizado!")

                st.rerun()

    else:
        st.info("Sem itens no estoque.")