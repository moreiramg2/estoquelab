import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG GOOGLE SHEETS
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
# FUNÇÃO PRA CARREGAR DADOS
# =========================
@st.cache_data(ttl=60)
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["nome", "lote", "quantidade", "status_validacao"])

    return df

df = load_data()

# =========================
# TÍTULO
# =========================
st.title("🧪 Estoque de Reagentes")

# =========================
# CADASTRAR REAGENTE
# =========================
st.subheader("➕ Adicionar reagente")

with st.form("add_form"):
    nome = st.text_input("Nome do reagente")
    lote = st.text_input("Lote")
    quantidade = st.number_input("Quantidade", min_value=1)
    status_validacao = st.selectbox(
        "Status de validação",
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
        st.success("✅ Reagente adicionado!")
        st.cache_data.clear()
        st.rerun()

# =========================
# MOSTRAR ESTOQUE
# =========================
st.subheader("📦 Estoque atual")

if not df.empty:
    df["id_item"] = df["nome"].astype(str) + " | Lote: " + df["lote"].astype(str)
    st.dataframe(df)

# =========================
# RETIRAR REAGENTE
# =========================
st.subheader("➖ Retirar reagente")

if not df.empty:

    item_selecionado = st.selectbox(
        "Selecione o item",
        df["id_item"]
    )

    quantidade_retirada = st.number_input(
        "Quantidade a retirar",
        min_value=1
    )

    if st.button("Retirar"):

        idx = df[df["id_item"] == item_selecionado].index[0]

        quantidade_atual = int(df.loc[idx, "quantidade"])

        if quantidade_retirada > quantidade_atual:
            st.error("❌ Quantidade maior que o estoque!")

        else:
            nova_qtd = quantidade_atual - quantidade_retirada

            if nova_qtd == 0:
                # Deleta linha quando zera
                sheet.delete_rows(idx + 2)
                st.warning("🗑️ Lote zerado e removido!")

            else:
                # Atualiza quantidade
                sheet.update_cell(idx + 2, 3, int(nova_qtd))
                st.success("✅ Estoque atualizado!")

            st.cache_data.clear()
            st.rerun()

else:
    st.info("Nenhum item cadastrado ainda.")