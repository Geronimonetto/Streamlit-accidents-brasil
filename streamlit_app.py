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

# Tamanho da população de cada estado - Fonte: https://www.cnnbrasil.com.br/nacional/brasil-tem-2125-milhoes-de-habitantes-diz-ibge/#goog_rewarded
populacao = {
    "SP": 45973194, "MG": 21322691, "RJ": 17219679, "BA": 14850513, "PR": 11824665,
    "RS": 11229915, "PE": 9539029, "CE": 9233656, "PA": 8664306, "SC": 8058441,
    "GO": 7350483, "MA": 7010960, "AM": 4281209, "PB": 4145040, "ES": 4102129,
    "MT": 3836399, "RN": 3446071, "PI": 3375646, "AL": 3220104, "DF": 2982818,
    "MS": 2901895, "SE": 2291077, "RO": 1746227, "TO": 1577342, "AC": 880631,
    "AP": 802837, "RR": 716793
}

# Criar dataframe com nomes, siglas e populações dos estados
estados = pd.DataFrame(estado_nome.items(), columns=['estado', 'sigla'])
estados['populacao'] = estados['sigla'].map(populacao)

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

# Acrescentar dados de acidentes e mortes + taxas no dataframe estados
estados['Acidentes'] = estados['sigla'].map(df['data_inversa'].groupby(df['uf']).count())
estados['Mortos'] = estados['sigla'].map(df['mortos'].groupby(df['uf']).sum())
estados['tx_acidentalidade_1k'] = estados['Acidentes'] / estados['populacao'] * 1000
estados['tx_mortalidade_1k'] = estados['Mortos'] / estados['populacao'] * 1000

# Sidebar
st.sidebar.header("Filtros")

# Criar dicionário de mapeamento sigla -> nome completo
mapa_estados = dict(zip(estados["sigla"], estados["estado"]))
uf_list = sorted([mapa_estados[sigla] for sigla in df["uf"].unique()])
uf_list = ['Brasil'] + list(uf_list)

# Definir intervalo de data possível de ser selecionado
min_date = df['data_acidente'].min().date()
max_date = df['data_acidente'].max().date()

# Função de limpar filtros
def reset():
    st.session_state.selected_uf = "Brasil"
    st.session_state.municipio = "Todos os Municípios"
    st.session_state.start_date = min_date
    st.session_state.end_date = max_date
    print('Limpar Filtros')

# Estados e Datas com estados padrão
if "selected_uf" not in st.session_state:
    st.session_state.selected_uf = "Brasil"
if "municipio" not in st.session_state:
    st.session_state.municipio = "Todos os Municípios"
if "start_date" not in st.session_state:
    st.session_state.start_date = df["data_acidente"].min().date()
if "end_date" not in st.session_state:
    st.session_state.end_date = df["data_acidente"].max().date()

# Filtro de UF
selected_uf = st.sidebar.selectbox("Estado", uf_list, index=uf_list.index(st.session_state.selected_uf), key = 'selected_uf')

# Filtro de Município (somente se um estado for selecionado)
municipio = None
if selected_uf != 'Brasil':
    uf_sigla = estado_nome[selected_uf]  # Pegamos a sigla usando o dicionário
    municipios_list = sorted(df[df['uf'] == uf_sigla]['municipio'].unique())
    municipios_list = ['Todos os Municípios'] + list(municipios_list)
    
    municipio = st.sidebar.selectbox("Município", municipios_list, index=municipios_list.index(st.session_state.municipio), key = 'municipio')

# Filtro de Data
st.sidebar.header("Selecione o intervalo de Data")

# Criar colunas para exibir os campos lado a lado
col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("**Início**", value=min_date, min_value=min_date, max_value=max_date, key="start_date")
end_date = col2.date_input("**Fim**", value=max_date, min_value=min_date, max_value=max_date, key="end_date")

# Converter para datetime
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Botão de limpar filtros
st.sidebar.button("Limpar Filtros", on_click=reset)

# Aplicar filtros
df_filtered = df.copy()

# Filtro de UF
if selected_uf != 'Brasil':
    uf_sigla = estado_nome[selected_uf]  # Pegamos a sigla usando o dicionário
    df_filtered = df_filtered[df_filtered['uf'] == uf_sigla]
    
    # Filtro de Município
    if municipio and municipio != 'Todos os Municípios':
        df_filtered = df_filtered[df_filtered['municipio'] == municipio]

# Filtro de Data
df_filtered = df_filtered[
    (df_filtered['data_acidente'] >= start_date) & 
    (df_filtered['data_acidente'] <= end_date)
]

# Exibir a bandeira do estado selecionado (se não for "Brasil")
if selected_uf != 'Brasil':
    uf_sigla = estado_nome[selected_uf]  # Pegamos a sigla usando o dicionário
    st.sidebar.image(bandeiras[uf_sigla], caption=f"Bandeira de {selected_uf}")
# Exibir a bandeira do Brasil, se não tiver um estado selecionado
else:
    st.sidebar.image(bandeiras[selected_uf], caption=f"Bandeira do Brasil")
# Calcular o total de acidentes no DataFrame filtrado
df_total_acidentes = float(df_filtered.value_counts().sum())
# Contar a quantidade de acidentes por dia
acidentes_por_dia = df_filtered.groupby(df_filtered['data_acidente'].dt.date).size()

# Calcular a média de acidentes por dia
media_acidentes_por_dia = acidentes_por_dia.mean()
media_acidentes_por_dia = f"{media_acidentes_por_dia:.2f}"
df_mortos = df_filtered[df_filtered['mortos'] != 0].value_counts().sum()

# Calcular taxa de acidentalidade e mortalidade Brasil
if selected_uf == 'Brasil':
    pop = estados['populacao'].sum()
else:
    pop = estados['populacao'][estados['estado'] == selected_uf].values[0]
tx_acid = df_total_acidentes / pop * 1000
tx_mort = df_mortos / pop * 1000

# KPIs
with st.container():
    # Criando uma coluna única
    col1 = st.columns(1)
    with col1[0]:
        subcol1, subcol2, subcol3, subcol4 = st.columns(4)
        
        # Ajustando o estilo de cada subcoluna
        subcol1.markdown(
            f'<div style="background-color: #222538; padding: 10px; border-radius: 5px;">'
            f'<h3 style="color: white; font-size: 16px;">Quantidade de acidentes</h3>'
            f'<p style="color: white; font-size: 30px; font-weight: bold;">{df_total_acidentes:.0f}</p></div>',
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
        subcol4.markdown(
            f'<div style="background-color: #222538; padding: 10px; border-radius: 5px;">'
            f'<h3 style="color: white; font-size: 16px;">Taxa de acidentalidade em BRs</h3>'
            f'<p style="color: white; font-size: 30px; font-weight: bold;">{tx_acid:.2f} <span style="font-size: 14px; font-weight: normal;">acidentes por mil habitantes</span></p></div>',
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

            # Identificar a maior barra
            maior_barra_index = df_dias["Quantidade"].idxmax()

            # Adicionar o texto de forma condicional para as barras
            text_position = ['outside'] * len(df_dias)  # Todos os rótulos inicialmente fora
            text_position[maior_barra_index] = 'inside'  # Alterar o rótulo da maior barra para dentro

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
                textposition=text_position,  # Aplicar as posições do texto
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
        tab1, tab2 = st.tabs(['Acidentes', 'Mortes'])
        with tab1:
            # Criar gráfico de linha com altura fixa
            fig1 = px.line(
                df_anos,
                x=df_anos.index,
                y='Quantidade de Acidentes',
                markers=True,  # Para adicionar marcadores nos pontos
                color_discrete_map={'Quantidade de Acidentes': '#fcde9c'}  # Cor personalizada
            )

            fig1.update_layout(height=445, paper_bgcolor="#222538", plot_bgcolor="#222538", title={
                "text": "Evolução de Acidentes por Ano",
                "x": 0.5,  # Centraliza o título
                "y": 0.95,  # Ajusta a posição vertical
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=20, family="Arial", color="white")  # Aumentando tamanho e mudando fonte
            })  # Altura fixa

            st.plotly_chart(fig1, use_container_width=True)
        with tab2:
            # Criar gráfico de linha com altura fixa
            fig3 = px.line(
                df_anos,
                x=df_anos.index,
                y='Quantidade de Mortes',
                markers=True,  # Para adicionar marcadores nos pontos
                color_discrete_map={
                    'Quantidade de Mortes': '#e24c70',  # Cor personalizada
                }
                
            )

            fig3.update_layout(height=445, paper_bgcolor="#222538", plot_bgcolor="#222538", title={
                "text": "Evolução de Mortes por Ano",
                "x": 0.5,  # Centraliza o título
                "y": 0.95,  # Ajusta a posição vertical
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=20, family="Arial", color="white")  # Aumentando tamanho e mudando fonte
            })  # Altura fixa

            st.plotly_chart(fig3, use_container_width=True)
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


