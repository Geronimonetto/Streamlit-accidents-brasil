# %%

import streamlit as st
import pandas as pd
import tarfile
import plotly.express as px
import requests
import plotly.graph_objects as go
from utils.routes import bandeiras
from modules.nav import navbar


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
navbar()
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
df = df.sort_values('data_acidente')
df['Month'] = df['data_acidente'].apply(lambda x: str(x.year) + "-" + str(x.month))


# Sidebar
st.sidebar.header("Filtros")

# Filtro de UF
uf_list = df["uf"].unique()
uf_list = ['Todos os Estados'] + list(uf_list)
uf = st.sidebar.selectbox("Estado", uf_list)
# Filtro de Município condicional
municipio = None
if uf != 'Todos os Estados':
    municipios_list = df[df['uf'] == uf]['municipio'].unique()
    municipios_list = ['Todos os Municípios'] + list(municipios_list)
    municipio = st.sidebar.selectbox("Município", municipios_list)
# Filtro de Data
st.sidebar.header("Filtros de Data")
min_date = df['data_acidente'].min().date()
max_date = df['data_acidente'].max().date()
selected_dates = st.sidebar.date_input(
    "Selecione o intervalo de datas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Processar datas selecionadas
if len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

# Converter para datetime
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Aplicar filtros
df_filtered = df.copy()

# Filtro de UF
if uf != 'Todos os Estados':
    df_filtered = df_filtered[df_filtered['uf'] == uf]
    
    # Filtro de Município
    if municipio and municipio != 'Todos os Municípios':
        df_filtered = df_filtered[df_filtered['municipio'] == municipio]

# Filtro de Data
df_filtered = df_filtered[
    (df_filtered['data_acidente'] >= start_date) & 
    (df_filtered['data_acidente'] <= end_date)
]

# Exibir a bandeira do estado selecionado (se não for "Todos os Estados")
if uf != 'Todos os Estados' and uf in bandeiras:
    st.sidebar.image(bandeiras[uf], caption=f"Bandeira de {uf}")
# Calcular o total de acidentes no DataFrame filtrado
df_total_acidentes = float(df_filtered.value_counts().sum())
# Contar a quantidade de acidentes por dia
acidentes_por_dia = df_filtered.groupby(df_filtered['data_acidente'].dt.date).size()

# Calcular a média de acidentes por dia
media_acidentes_por_dia = acidentes_por_dia.mean()
media_acidentes_por_dia = f"{media_acidentes_por_dia:.2f}"
df_mortos = df_filtered[df_filtered['mortos'] != 0].value_counts().sum()
with st.container():
    # Criando uma coluna única
    col1 = st.columns(1)
    with col1[0]:
        subcol1, subcol2, subcol3 = st.columns(3)
        
        # Ajustando o estilo de cada subcoluna
        subcol1.markdown(
            f'<div style="background-color: #222538; padding: 10px; border-radius: 5px;">'
            f'<h3 style="color: white; font-size: 16px;">Quantidade de acidentes</h3>'
            f'<p style="color: white; font-size: 30px; font-weight: bold;">{df_total_acidentes}</p></div>',
            unsafe_allow_html=True
        )
        subcol2.markdown(
            f'<div style="background-color: #222538; padding: 10px; border-radius: 5px;">'
            f'<h3 style="color: white; font-size: 16px;">Quantidade de mortos em acidentes</h3>'
            f'<p style="color: white; font-size: 30px; font-weight: bold;">{df_mortos}</p></div>',
            unsafe_allow_html=True
        )
        subcol3.markdown(
            f'<div style="background-color: #222538; padding: 10px; border-radius: 5px;">'
            f'<h3 style="color: white; font-size: 16px;">Média de acidentes por dia</h3>'
            f'<p style="color: white; font-size: 30px; font-weight: bold;">{media_acidentes_por_dia}</p></div>',
            unsafe_allow_html=True
        )
    
    # Adicionando um pequeno espaço entre os containers
    st.markdown("<br>", unsafe_allow_html=True)

### Dashboard 1
# Contagem de acidentes por estado
df_mapa = df_filtered.groupby("uf").size().reset_index(name="Quantidade de Acidentes") 

with st.container():
    col1, col2 = st.columns([0.6, 0.4]) 
    
    with col1:
        # Criar mapa de calor dos acidentes por estado
        fig_mapa = px.choropleth(
            df_mapa,
            geojson=geojson,
            locations='uf',
            featureidkey="id",
            color='Quantidade de Acidentes',
            color_continuous_scale='sunsetdark',
            labels={'Quantidade de Acidentes': 'Número de Acidentes'}
        )
        

        fig_mapa.update_geos(fitbounds="locations", visible=False, bgcolor='rgba(0,0,0,0)', projection_scale=2.0, projection_type="orthographic" )
        fig_mapa.update_layout(coloraxis_colorbar_title=None ,height=1000, width=600, paper_bgcolor="#222538", plot_bgcolor="#222538", title={
                "text": "Quantidade de Acidentes por Estado",
                "x": 0.5,  # Centraliza o título
                "y": 0.95,  # Ajusta a posição vertical
                "xanchor": "right",
                "yanchor": "top",
                "font": dict(size=20, family="Arial", color="white")  # Aumentando tamanho e mudando fonte
            },) # Ajustando altura e largura do gráfico

        col1.plotly_chart(fig_mapa)  # Removido use_container_width=True
    
    with col2:
        # Criando o gráfico de pizza
        df_classificacao = df_filtered.groupby("classificacao_acidente").size().reset_index(name="Quantidade por tipo")
        cores = ["#fcde9c", "#e24c70", "#f58a72"]

        fig_pizza = go.Figure(go.Pie(
            labels=df_classificacao["classificacao_acidente"],
            values=df_classificacao["Quantidade por tipo"],
            marker=dict(colors=cores)
        ))
        fig_pizza.update_layout(
            title={
                "text": "Quantidade de Acidentes por Classificação",
                "x": 0.5,
                "y": 0.95,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=20, family="Arial", color="white")
            },
            height=400,
            paper_bgcolor="#222538",
            plot_bgcolor="#222538",
            margin=dict(l=50, r=50, t=100, b=50)  # Ajustando as margens
        )
        col2.plotly_chart(fig_pizza)

        # Adicionando o gráfico abaixo do gráfico de pizza
        with st.container():
            # Criando o gráfico de barras horizontal
            df_dias = df_filtered.groupby("fase_dia").size().reset_index(name="Quantidade")

            fig_barras = go.Figure(go.Bar(
                y=df_dias["fase_dia"],
                x=df_dias["Quantidade"],
                orientation='h',
                marker=dict(
                    color=df_dias["Quantidade"],
                    colorscale='sunsetdark',
                    showscale=False
                ),
                text=df_dias["Quantidade"],
                textposition='outside',
            ))

            fig_barras.update_layout(
                title={
                    "text": "Quantidade de Acidentes por Fase do Dia",
                    "x": 0.5,
                    "y": 0.95,
                    "xanchor": "center",
                    "yanchor": "top",
                    "font": dict(size=20, family="Arial", color="white")
                },
                height=585,
                paper_bgcolor="#222538",
                plot_bgcolor="#222538",
                margin=dict(l=100, r=50, t=50, b=100),  # Ajustando as margens
                bargap=0.2
            )

            col2.plotly_chart(fig_barras)

# Criar DataFrame com a contagem de acidentes e mortes por ano
df_anos = (
    df_filtered.groupby(df_filtered['data_acidente'].dt.year)
    .agg(acidentes=('data_acidente', 'count'), mortes=('mortos', 'sum'))
    .reset_index()
)
df_anos.columns = ['Ano', 'Quantidade de Acidentes', 'Quantidade de Mortes']
df_anos.set_index('Ano', inplace=True)

with st.container():

    col3, col4 = st.columns(2)
    with col3:
        # Criar gráfico de linha com altura fixa
        fig1 = px.line(
            df_anos,
            x=df_anos.index,
            y=['Quantidade de Acidentes', 'Quantidade de Mortes'],
            markers=True,  # Para adicionar marcadores nos pontos
            color_discrete_map={
                'Quantidade de Acidentes': '#fcde9c',  # Cor personalizada
                'Quantidade de Mortes': '#e24c70'      # Cor personalizada
            }
            
        )

        fig1.update_layout(height=500, paper_bgcolor="#222538", plot_bgcolor="#222538", title={
            "text": "Evolução de Acidentes e Mortes por Ano",
            "x": 0.5,  # Centraliza o título
            "y": 0.95,  # Ajusta a posição vertical
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=20, family="Arial", color="white")  # Aumentando tamanho e mudando fonte
        })  # Altura fixa

        col3.plotly_chart(fig1, use_container_width=True)
    with col4:
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
            color_continuous_scale='sunsetdark',  # Escolha a paleta que você preferir
            labels={'dia_semana': 'Dia da Semana', 'accident_count': 'Número de Acidentes'} 
        )

        fig2.update_traces(textposition='outside')
        fig2.update_layout(height=500, paper_bgcolor="#222538", plot_bgcolor="#222538", title={
            "text": "Frequência de acidentes por dia da semana",
            "x": 0.5,  # Centraliza o título
            "y": 0.95,  # Ajusta a posição vertical
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=20, family="Arial", color="white")  # Aumentando tamanho e mudando fonte
        })  # Altura fixa
        col4.plotly_chart(fig2, use_container_width=True)


