import streamlit as st
import pandas as pd
from datetime import datetime

df = pd.read_csv("estoque.csv")

st.title("🧪 Estoque do Laboratório")

criticos = df[df["quantidade_atual"] <= df["quantidade_minima"]]

validade = pd.to_datetime(df["validade"])
vencendo = df[validade <= datetime.now() + pd.Timedelta(days=30)]

st.metric("Itens críticos", len(criticos))
st.metric("Próximos da validade", len(vencendo))

st.subheader("📦 Estoque")
st.dataframe(df)

st.subheader("⚠️ Críticos")
st.dataframe(criticos)

st.subheader("⏳ Validade próxima")
st.dataframe(vencendo)