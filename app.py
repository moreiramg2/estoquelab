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

# 🔴 COLE O ID DA SUA PLANILHA AQUI
SHEET_ID = 1tmsV_1h78N3NINJZ6yj6OUGOVxbgeQQikadIzTEKyGk

sheet = client.open_by_key(SHEET_ID).sheet1

data = sheet.get_all_records()
df = pd.DataFrame(data)

if df.empty:
    df = pd.DataFrame(columns=["nome", "quantidade_atual", "quantidade_minima", "validade", "local"])

df["validade"] = pd.to_datetime(df["validade"], errors='coerce')

# ===== TÍTULO =====
st.title("🧪 Dashboard de Estoque do Laboratório")

# ===== FORMULÁRIO =====
st.subheader("➕ Adicionar novo reagente")

with st.form("formulario"):
    nome = st.text_input("Nome do reagente")
    quantidade = st.number_input("Quantidade atual", min_value=0)
    minimo = st.number_input("Quantidade mínima", min_value=0)
    validade = st.date_input("Data de validade")
    local = st.text_input("Local")

    submitted = st.form_submit_button("Adicionar")

    if submitted:
        sheet.append_row([
            nome,
            quantidade,
            minimo,
            str(validade),
            local
        ])
        st.success("✅ Reagente adicionado!")

# ===== REGRAS =====
criticos = df[df["quantidade_atual"] <= df["quantidade_minima"]]
vencendo = df[df["validade"] <= datetime.now() + pd.Timedelta(days=30)]

# ===== CARDS =====
col1, col2, col3 = st.columns(3)

col1.metric("📦 Total", len(df))
col2.metric("⚠️ Críticos", len(criticos))
col3.metric("⏳ Vencendo", len(vencendo))

st.divider()

# ===== STATUS =====
def status(row):
    if row["quantidade_atual"] <= row["quantidade_minima"]:
        return "🔴 Crítico"
    elif row["validade"] <= datetime.now() + pd.Timedelta(days=30):
        return "🟡 Atenção"
    else:
        return "🟢 OK"

if not df.empty:
    df["Status"] = df.apply(status, axis=1)

# ===== TABELA =====
st.dataframe(df, use_container_width=True)