import streamlit as st
import pandas as pd
import tarfile
import plotly.express as px
import requests
# Baixar o GeoJSON dos estados brasileiros
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
response = requests.get(geojson_url)
geojson = response.json()

# Criar um dicionário de conversão do nome dos estados no GeoJSON
estado_nome = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA', 'Ceará': 'CE',
    'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão': 'MA', 'Mato Grosso': 'MT',
    'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG', 'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR',
    'Pernambuco': 'PE', 'Piauí': 'PI', 'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN',
    'Rio Grande do Sul': 'RS', 'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC',
    'São Paulo': 'SP', 'Sergipe': 'SE', 'Tocantins': 'TO'
}

# Ajustar os nomes no GeoJSON para corresponder ao DataFrame
for feature in geojson['features']:
    nome_estado = feature['properties']['name']
    feature['id'] = estado_nome.get(nome_estado, None)  # Adicionar ID com a sigla do estado

# Configuração do layout do app
st.set_page_config(page_title="Análise de Acidentes de Trânsito", layout="wide")

# Caminho do arquivo .tar.gz
tar_path = "./data/accidents_2017_to_2023.tar.gz"

# Dicionário de bandeiras (Wikimedia)
bandeiras = {
    "AC": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Bandeira_do_Acre.svg",
    "AL": "https://upload.wikimedia.org/wikipedia/commons/8/88/Bandeira_de_Alagoas.svg",
    "AP": "https://upload.wikimedia.org/wikipedia/commons/0/0c/Bandeira_do_Amapá.svg",
    "AM": "https://upload.wikimedia.org/wikipedia/commons/6/6b/Bandeira_do_Amazonas.svg",
    "BA": "https://upload.wikimedia.org/wikipedia/commons/2/28/Bandeira_da_Bahia.svg",
    "CE": "https://upload.wikimedia.org/wikipedia/commons/2/2e/Bandeira_do_Ceará.svg",
    "DF": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Bandeira_do_Distrito_Federal_%28Brasil%29.svg",
    "ES": "https://upload.wikimedia.org/wikipedia/commons/4/43/Bandeira_do_Espírito_Santo.svg",
    "GO": "https://upload.wikimedia.org/wikipedia/commons/b/be/Bandeira_de_Goiás.svg",
    "MA": "https://upload.wikimedia.org/wikipedia/commons/4/45/Bandeira_do_Maranhão.svg",
    "MT": "https://upload.wikimedia.org/wikipedia/commons/0/0b/Bandeira_de_Mato_Grosso.svg",
    "MS": "https://upload.wikimedia.org/wikipedia/commons/6/64/Bandeira_de_Mato_Grosso_do_Sul.svg",
    "MG": "https://upload.wikimedia.org/wikipedia/commons/f/f4/Bandeira_de_Minas_Gerais.svg",
    "PA": "https://upload.wikimedia.org/wikipedia/commons/0/02/Bandeira_do_Pará.svg",
    "PB": "https://upload.wikimedia.org/wikipedia/commons/b/bb/Bandeira_da_Paraíba.svg",
    "PR": "https://upload.wikimedia.org/wikipedia/commons/9/93/Bandeira_do_Paraná.svg",
    "PE": "https://upload.wikimedia.org/wikipedia/commons/5/59/Bandeira_de_Pernambuco.svg",
    "PI": "https://upload.wikimedia.org/wikipedia/commons/3/33/Bandeira_do_Piauí.svg",
    "RJ": "https://upload.wikimedia.org/wikipedia/commons/7/73/Bandeira_do_estado_do_Rio_de_Janeiro.svg",
    "RN": "https://upload.wikimedia.org/wikipedia/commons/7/70/Bandeira_do_Rio_Grande_do_Norte.svg",
    "RS": "https://upload.wikimedia.org/wikipedia/commons/6/63/Bandeira_do_Rio_Grande_do_Sul.svg",
    "RO": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Bandeira_de_Rondônia.svg",
    "RR": "https://upload.wikimedia.org/wikipedia/commons/9/98/Bandeira_de_Roraima.svg",
    "SC": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Bandeira_de_Santa_Catarina.svg",
    "SP": "https://upload.wikimedia.org/wikipedia/commons/2/2b/Bandeira_do_estado_de_São_Paulo.svg",
    "SE": "https://upload.wikimedia.org/wikipedia/commons/b/be/Bandeira_de_Sergipe.svg",
    "TO": "https://upload.wikimedia.org/wikipedia/commons/f/ff/Bandeira_do_Tocantins.svg"
}

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
df = df.sort_values('data_acidente')
df['Month'] = df['data_acidente'].apply(lambda x: str(x.year) + "-" + str(x.month))

# Sidebar
st.sidebar.header("Filtros")
uf_list = df["uf"].unique()
uf = st.sidebar.selectbox("Estado", uf_list)
df_filtered = df[df['uf'] == uf]


# Exibir a bandeira do estado selecionado
if uf in bandeiras:
    st.sidebar.image(bandeiras[uf], caption=f"Bandeira de {uf}")


# Contagem de acidentes por estado
df_mapa = df.groupby("uf").size().reset_index(name="Quantidade de Acidentes")

# Criar mapa de calor dos acidentes por estado
fig_mapa = px.choropleth(
    df_mapa,
    geojson=geojson,
    locations='uf',
    featureidkey="id",
    color='Quantidade de Acidentes',
    color_continuous_scale='Reds',
    title='Quantidade de Acidentes por Estado',
    labels={'Quantidade de Acidentes': 'Número de Acidentes'}
)

fig_mapa.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig_mapa, use_container_width=True)

# Layout de duas colunas
col1, col2 = st.columns(2)

# Criar DataFrame com a contagem de acidentes e mortes por ano
df_anos = (
    df_filtered.groupby(df_filtered['data_acidente'].dt.year)
    .agg(acidentes=('data_acidente', 'count'), mortes=('mortos', 'sum'))
    .reset_index()
)
df_anos.columns = ['Ano', 'Quantidade de Acidentes', 'Quantidade de Mortes']
df_anos.set_index('Ano', inplace=True)
# Criar gráfico de linha com altura fixa
fig1 = px.line(
    df_anos,
    x=df_anos.index,
    y=['Quantidade de Acidentes', 'Quantidade de Mortes'],
    markers=True,
    color_discrete_sequence=['Yellow', 'Red'],  # Mantendo a sequência de cores discretas
    title="Evolução de Acidentes e Mortes por Ano"
)

fig1.update_layout(height=400)  # Altura fixa

col1.plotly_chart(fig1, use_container_width=True)
# Agrupar os dados por dia da semana e contar os acidentes
day_accidents = df_filtered['dia_semana'].value_counts().reset_index()
day_accidents.columns = ['dia_semana', 'accident_count']

# Ordenar os dias corretamente
dias_ordenados = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
day_accidents['dia_semana'] = pd.Categorical(day_accidents['dia_semana'], categories=dias_ordenados, ordered=True)
day_accidents = day_accidents.sort_values('dia_semana')

fig2 = px.bar(
    day_accidents, 
    x='dia_semana', 
    y='accident_count', 
    text='accident_count', 
    color='accident_count',
    color_continuous_scale='Reds',  # Escolha a paleta que você preferir
    labels={'dia_semana': 'Dia da Semana', 'accident_count': 'Número de Acidentes'},
    title='Número de Acidentes por Dia da Semana'
)

fig2.update_traces(textposition='outside')
fig2.update_layout(height=400)  # Altura fixa



col2.plotly_chart(fig2, use_container_width=True)

# Exibir dataframe filtrado
st.dataframe(df_filtered)
