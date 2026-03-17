import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Estoque Lab", layout="wide")

# ===== CONECTAR GOOGLE SHEETS =====
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope)

client = gspread.authorize(creds)

SHEET_ID = "1tmsV_1h78N3NINJZ6yj6OUGOVxbgeQQikadIzTEKyGk"
sheet = client.open_by_key(SHEET_ID).sheet1

# ===== CACHE =====
@st.cache_data(ttl=60)
def carregar_dados():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = carregar_dados()

# ===== GARANTIR COLUNAS =====
if df.empty:
    df = pd.DataFrame(columns=[
        "nome", "lote", "quantidade_atual",
        "quantidade_minima", "validade",
        "status_validacao", "local"
    ])

df["validade"] = pd.to_datetime(df["validade"], errors='coerce')

# ===== TÍTULO =====
st.title("🧪 Controle de Estoque do Laboratório")

# ===== FORMULÁRIO =====
st.subheader("➕ Adicionar novo lote")

with st.form("formulario"):
    nome = st.text_input("Nome do reagente")
    lote = st.text_input("Lote")
    quantidade = st.number_input("Quantidade atual", min_value=0)
    minimo = st.number_input("Quantidade mínima", min_value=0)
    validade = st.date_input("Validade")
    status_validacao = st.selectbox(
        "Status de validação",
        ["Aprovado", "Pendente", "Reprovado"]
    )
    local = st.text_input("Local")

    submitted = st.form_submit_button("Adicionar")

    if submitted:
        sheet.append_row([
            nome,
            lote,
            quantidade,
            minimo,
            str(validade),
            status_validacao,
            local
        ])
        st.success("✅ Lote adicionado!")
        st.cache_data.clear()
        st.rerun()

# ===== REGRAS =====
criticos = df[df["quantidade_atual"] <= df["quantidade_minima"]]
vencendo = df[df["validade"] <= datetime.now() + pd.Timedelta(days=30)]

# ===== CARDS =====
col1, col2, col3 = st.columns(3)

col1.metric("📦 Total de lotes", len(df))
col2.metric("⚠️ Críticos", len(criticos))
col3.metric("⏳ Vencendo", len(vencendo))

st.divider()

# ===== STATUS =====
def status(row):
    if row["status_validacao"] == "Reprovado":
        return "⛔ Reprovado"
    elif row["quantidade_atual"] <= row["quantidade_minima"]:
        return "🔴 Crítico"
    elif row["validade"] <= datetime.now() + pd.Timedelta(days=30):
        return "🟡 Vencendo"
    else:
        return "🟢 OK"

if not df.empty:
    df["Status"] = df.apply(status, axis=1)

# ===== FILTRO (NOVO 🔍) =====
busca = st.text_input("🔍 Buscar reagente")

if busca:
    df = df[df["nome"].str.contains(busca, case=False, na=False)]

# ===== TABELA =====
st.dataframe(df, use_container_width=True)
st.divider()
st.subheader("➖ Retirar do estoque")

if not df.empty:

    # Criar identificação única (nome + lote)
    df["id_item"] = (
    df["nome"].fillna("Sem nome").astype(str) +
    " | Lote: " +
    df["lote"].fillna("Sem lote").astype(str)
)

    item_selecionado = st.selectbox(
        "Selecione o item",
        df["id_item"]
    )

    quantidade_retirada = st.number_input(
        "Quantidade a retirar",
        min_value=0
    )

    if st.button("Retirar"):

        # Encontrar índice do item
        idx = df[df["id_item"] == item_selecionado].index[0]

        quantidade_atual = df.loc[idx, "quantidade_atual"]

    if quantidade_retirada > quantidade_atual:
    st.error("❌ Quantidade maior que o estoque!")

else:
    nova_qtd = quantidade_atual - quantidade_retirada

    if nova_qtd == 0:
        # Deleta a linha (lote acabou)
        sheet.delete_rows(idx + 2)
        st.warning("🗑️ Lote zerado e removido do estoque!")

    else:
        # Atualiza normalmente
        sheet.update_cell(idx + 2, 3, int(nova_qtd))
        st.success("✅ Estoque atualizado!")

    st.cache_data.clear()
    st.rerun()