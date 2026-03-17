import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Estoque Lab", layout="wide")

df = pd.read_csv("estoque.csv")

# Título
st.title("🧪 Dashboard de Estoque do Laboratório")

# Converter datas
df["validade"] = pd.to_datetime(df["validade"])

# Regras
criticos = df[df["quantidade_atual"] <= df["quantidade_minima"]]
vencendo = df[df["validade"] <= datetime.now() + pd.Timedelta(days=30)]

# ===== CARDS =====
col1, col2, col3 = st.columns(3)

col1.metric("📦 Total de Insumos", len(df))
col2.metric("⚠️ Itens Críticos", len(criticos))
col3.metric("⏳ Próximos do Vencimento", len(vencendo))

st.divider()

# ===== BUSCA =====
busca = st.text_input("🔍 Buscar reagente")

if busca:
    df = df[df["nome"].str.contains(busca, case=False)]

# ===== STATUS COLORIDO =====
def status(row):
    if row["quantidade_atual"] <= row["quantidade_minima"]:
        return "🔴 Crítico"
    elif row["validade"] <= datetime.now() + pd.Timedelta(days=30):
        return "🟡 Atenção"
    else:
        return "🟢 OK"

df["Status"] = df.apply(status, axis=1)

# ===== TABELA PRINCIPAL =====
st.subheader("📋 Visão Geral do Estoque")
st.dataframe(df, use_container_width=True)

st.divider()

# ===== SEÇÃO CRÍTICOS =====
st.subheader("⚠️ Insumos Críticos")
st.dataframe(criticos, use_container_width=True)

# ===== SEÇÃO VALIDADE =====
st.subheader("⏳ Próximos do Vencimento")
st.dataframe(vencendo, use_container_width=True)