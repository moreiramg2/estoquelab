import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG GOOGLE SHEETS
# =========================
SHEET_ID = "COLE_AQUI_O_ID_DA_PLANILHA"

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
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["nome", "lote", "quantidade", "status_validacao"])

    # Padroniza nomes das colunas
    df.columns = df.columns.str.strip().str.lower()

    return df

df = load_data()

# =========================
# FILTRA ITENS COM QUANTIDADE > 0
# =========================
if not df.empty:
    df = df[df["quantidade"] > 0]

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
# MOSTRAR ESTOQUE COM CORES
# =========================
st.subheader("📦 Estoque atual")

if not df.empty:
    df["id_item"] = df["nome"].astype(str) + " | Lote: " + df["lote"].astype(str)

    # Função pra colorir status
    def highlight_status(val):
        if val == "Reprovado":
            return "color: red; font-weight: bold"
        elif val == "Aprovado":
            return "color: green; font-weight: bold"
        elif val == "Pendente":
            return "color: orange; font-weight: bold"
        else:
            return ""

    # Aplica cores na coluna de status
    st.dataframe(df.style.applymap(highlight_status, subset=["status_validacao"]))
else:
    st.info("Nenhum item cadastrado ainda.")

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
                sheet.delete_rows(int(idx) + 2)
                st.warning("🗑️ Lote zerado e removido do estoque!")

            else:
                # Atualiza quantidade
                sheet.update_cell(int(idx) + 2, 3, int(nova_qtd))
                st.success("✅ Estoque atualizado!")

            st.cache_data.clear()
            st.rerun()