import streamlit as st

def navbar():
    with st.sidebar:
        st.page_link('streamlit_app.py', label='Acidentes', icon='🚗')  # Ícone de carro para representar acidentes
        st.page_link('pages/mortalidade.py', label='Mortalidade', icon='⚰️')  # Ícone de caixão para representar fatalidades
