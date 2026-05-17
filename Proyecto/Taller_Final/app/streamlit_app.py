import streamlit as st
import sys
import os

# Añadir ruta para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agente_devoluciones import ejecutar_agente

st.set_page_config(page_title="Asistente EcoMarket", page_icon="🔄")
st.title("🔄 Agente de Devoluciones - EcoMarket")
st.markdown("Pregunta sobre políticas, inicia una devolución o consulta el inventario.")

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input del usuario
if prompt := st.chat_input("Escribe tu mensaje..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            respuesta = ejecutar_agente(prompt)
        st.markdown(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})