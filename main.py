# Importar bibliotecas
import streamlit as st
import pandas as pd
import tarfile

# Configuração do layout do app
st.set_page_config(page_title="Análise de Acidentes de Trânsito", layout="wide")

# Caminho do arquivo .tar.gz
tar_path = "./data/accidents_2017_to_2023.tar.gz"

# Função para carregar os dados
@st.cache_data
def load_df(tar_path):
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith(".csv"):
                with tar.extractfile(member) as file:
                    df = pd.read_csv(file)
                    break
    return df

# Carregar os dados
df = load_df(tar_path)

# Converter data para formato datetime
df['data_acidente'] = pd.to_datetime(df['data_inversa'] + " " + df['horario'], format='%Y-%m-%d %H:%M:%S')

# Excluir colunas desnecessárias
df = df.drop(columns=['delegacia', 'regional', 'data_inversa'])

# Criar DataFrame com a contagem de acidentes e mortes por ano
df_anos = (
    df.groupby(df['data_acidente'].dt.year)
    .agg(acidentes=('data_acidente', 'count'), mortes=('mortos', 'sum'))
    .reset_index()
)

# Renomear colunas corretamente
df_anos.columns = ['Ano', 'Quantidade de Acidentes', 'Quantidade de Mortes']

# Definir o índice como "Ano"
df_anos.set_index('Ano', inplace=True)

# Criar a interface do Streamlit
st.sidebar.title("Opções")
st.sidebar.write("Selecione os filtros desejados para análise.")

# Título principal
st.title("📊 APP de Análise de Acidentes de Trânsito")
st.write("O gráfico abaixo mostra a quantidade de **acidentes** e **mortes** por ano.")

# Criar o gráfico de linha
st.line_chart(df_anos)

# Rodapé
st.write("---")
st.write("📌 **Fim do projeto**")
