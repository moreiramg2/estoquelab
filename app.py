import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

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
        return pd.DataFrame(columns=["nome", "lote", "quantidade", "status_validacao", "validade"])

    df.columns = df.columns.str.strip().str.lower()

    if "validade" in df.columns:
        df["validade"] = pd.to_datetime(df["validade"], errors="coerce")

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

        # ===== ALERTAS =====
        st.subheader("🚨 Alertas")

        hoje = datetime.now()

        estoque_baixo = df[df["quantidade"] <= 5]
        vencendo = df[df["validade"] <= hoje + pd.Timedelta(days=30)]

        if not estoque_baixo.empty:
            st.warning(f"⚠️ {len(estoque_baixo)} itens com estoque baixo")

        if not vencendo.empty:
            st.error(f"📅 {len(vencendo)} itens próximos do vencimento")

        if estoque_baixo.empty and vencendo.empty:
            st.success("✅ Tudo sob controle!")

        st.divider()

        # ===== GRAFICO =====
        st.subheader("📊 Quantidade por reagente")

        grafico_qtd = df.groupby("nome")["quantidade"].sum().sort_values(ascending=False)
        st.bar_chart(grafico_qtd)

        st.divider()

        # ===== TABELA =====
        st.subheader("📋 Estoque atual")

        def highlight_row(row):
            if row["quantidade"] <= 5:
                return ["background-color: #fff3cd"] * len(row)
            elif pd.notnull(row["validade"]) and row["validade"] <= hoje + pd.Timedelta(days=30):
                return ["background-color: #f8d7da"] * len(row)
            return [""] * len(row)

        df["id_item"] = df["nome"].astype(str) + " | Lote: " + df["lote"].astype(str)

        st.dataframe(
            df.style.apply(highlight_row, axis=1),
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
        validade = st.date_input("Validade")
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
                status_validacao,
                str(validade)
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