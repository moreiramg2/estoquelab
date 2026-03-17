import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Estoque Lab", layout="wide")

# ===== CARREGAR DADOS =====
df = pd.read_csv("estoque.csv")

# Converter datas
df["validade"] = pd.to_datetime(df["validade"])

# ===== TÍTULO =====
st.title("🧪 Dashboard de Estoque do Laboratório")

# ===== FORMULÁRIO =====
st.subheader("➕ Adicionar novo reagente")

with st.form("formulario"):
    nome = st.text_input("Nome do reagente")
    quantidade = st.number_input("Quantidade atual", min_value=0)
    minimo = st.number_input("Quantidade mínima", min_value=0)
    validade = st.date_input("Data de validade")
    local = st.text_input("Local (ex: Freezer -20°C)")

    submitted = st.form_submit_button("Adicionar")

    if submitted:
        novo = pd.DataFrame({
            "nome": [nome],
            "quantidade_atual": [quantidade],
            "quantidade_minima": [minimo],
            "validade": [validade],
            "local": [local]
        })

        df = pd.concat([df, novo], ignore_index=True)
        df.to_csv("estoque.csv", index=False)

        st.success("✅ Reagente adicionado com sucesso!")

# ===== REGRAS =====
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

# ===== STATUS =====
def status(row):
    if row["quantidade_atual"] <= row["quantidade_minima"]:
        return "🔴 Crítico"
    elif row["validade"] <= datetime.now() + pd.Timedelta(days=30):
        return "🟡 Atenção"
    else:
        return "🟢 OK"

df["Status"] = df.apply(status, axis=1)

# ===== TABELA =====
st.subheader("📋 Estoque")
st.dataframe(df, use_container_width=True)

# ===== CRÍTICOS =====
st.subheader("⚠️ Insumos Críticos")
st.dataframe(criticos, use_container_width=True)

# ===== VALIDADE =====
st.subheader("⏳ Próximos do Vencimento")
st.dataframe(vencendo, use_container_width=True)