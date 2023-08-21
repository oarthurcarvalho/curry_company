import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from haversine import haversine
from datetime import datetime
from PIL import Image
import folium as fl
from streamlit_folium import folium_static

# ----------------------------------------
#                FUNÇÕES
# ----------------------------------------

def clean_data( df1 ):
    """
        Esta função tem a responsabilidade de limpar o dataframe

        Tipos de Limpeza:
            1. Remoção dos dados NaN
            2. Mudança do tipo da coluna de dados
            3. Remoção dos espaços das variáveis de texto
            4. Formatação da coluna de datas
            5. Limpeza da coluna de tempo ( remoção do texto da variável numérica )

            Input: Dataframe
            Output: Dataframe
    """

    ## 1. Selecionando as linhas que estão sem NaN
    cols = ['City', 'Festival', 'Road_traffic_density', 'Weatherconditions']
    df1[cols] = df1[cols].replace('NaN ', pd.NA)
    df1 = df1[
        (df1['City'].notna()) & (df1['Festival'].notna()) &
        (df1['Road_traffic_density'].notna()) & (df1['Weatherconditions'].notna())
    ]
    
    ## 2. Eliminando os espaços vazios ao final dos valores.
    cols_to_strip = [
        'ID', 'Delivery_person_ID', 'Road_traffic_density', 'Type_of_order',
        'Type_of_vehicle', 'Festival', 'City']
    df1[cols_to_strip] = df1[cols_to_strip].apply(lambda x: x.str.strip())
    
    ## 3. Transformando o tipo das colunas adequadamente
    cols_to_convert = ['Delivery_person_Age', 'Delivery_person_Ratings', 'multiple_deliveries']
    df1[cols_to_convert] = df1[cols_to_convert].apply(pd.to_numeric, errors='coerce')
    df1['Order_Date'] = pd.to_datetime(df1['Order_Date'], format='%d-%m-%Y')
    
    ## 4. Retirando sujeiros nos valores de algumas colunas
    df1['Weatherconditions'] = ( df1['Weatherconditions']
                                    .apply(lambda x: x.split()[-1]) )
    df1['Time_taken(min)'] = df1['Time_taken(min)'].apply(lambda x: x.split()[-1])
    df1['Time_taken(min)'] = df1['Time_taken(min)'].astype('int64')

    ## 5. Criação da coluna 'week_of_year
    df1['week_of_year'] = df1['Order_Date'].dt.strftime( '%U' ).astype('int64')

    return df1

def top_delivers( df1, top_asc=True ):
    media_tempo_por_city_entregador = df1.groupby(
    ['City', 'Delivery_person_ID'])['Time_taken(min)'].mean().round(2)
    
    df_aux = media_tempo_por_city_entregador.groupby(
        'City', group_keys=False)

    if top_asc == True:
        return df_aux.nlargest(10).reset_index()

    return df_aux.nsmallest(10).reset_index()

def ratings_by( df1, agg ):
    df_aux = ( df1.groupby(agg)
                  .agg( { 'Delivery_person_Ratings': ['mean', 'std'] })
                  .round(2) )

    df_aux.columns = ['mean', 'std']
    return df_aux
#=================================================================================================#
#                            INÍCIO DA ESTRUTURA LÓGICA DO CÓDIGO
#=================================================================================================

# IMPORT DATASET
df = pd.read_csv( 'dataset/train-delivery.csv' )

# LIMPEZA DO DATASET
df1 = clean_data( df )

#-----------------------------
# CONFIGURANDO STREAMLIT PAGE
#-----------------------------
st.set_page_config(
    page_title='Marketplace - Visão Entregadores',
    page_icon='img/curry.png', layout='wide'
)

#===========================================================
#                      BARRA LATERAL
#===========================================================
st.header( 'Marketplace - Visão Entregadores' )

image_path = 'img/curry.png'
image = Image.open( image_path )
st.sidebar.image( image, width=120 )

st.sidebar.markdown( '# Cury Company' )
st.sidebar.markdown( '## Fastest Delivery in Town' )
st.sidebar.markdown( """---""" )

st.sidebar.markdown( '## Selecione uma data limite' )
date_slider = st.sidebar.slider(
    'Até qual valor?',
    value=datetime( 2022, 4, 13 ),
    min_value=datetime( 2022, 2, 11),
    max_value=datetime( 2022, 4, 6 ),
    format='DD-MM-YYYY'
)
st.sidebar.markdown( """---""" )

traffic_options = st.sidebar.multiselect(
    "Quais as condições do trânsito?",
    ['Low', 'Medium', 'High', 'Jam'],
    default=['Low', 'Medium', 'High', 'Jam']
)

weather_options = st.sidebar.multiselect(
    "Quais as condições do trânsito?",
    df1['Weatherconditions'].unique(),
    default=df1['Weatherconditions'].unique()
)

st.sidebar.markdown( """---""" )
st.sidebar.markdown( 'Powered by Comunidade DS' )

# Filtro de data
linhas_selecionadas = df1['Order_Date'] < date_slider
df1 = df1.loc[linhas_selecionadas, : ]

# Filtro de transito
linhas_selecionadas = df1['Road_traffic_density'].isin( traffic_options )
df1 = df1.loc[linhas_selecionadas, : ]

# Filtro de transito
linhas_selecionadas = df1['Weatherconditions'].isin( weather_options )
df1 = df1.loc[linhas_selecionadas, : ]

#===========================================================
#                      LAYOUT DASHBOARD
#===========================================================
tab1, tab2, tab3 = st.tabs( ['Visão Gerencial', '_', '_'] )

with tab1:
    with st.container():

        st.markdown( '<h2 style="text-align: center;">Overall Metrics</h2>', unsafe_allow_html=True )
        col1, col2, col3, col4 = st.columns( 4, gap='large' )
    
        with col1:
            maior_idade_entregador = df1['Delivery_person_Age'].max()
            col1.metric( 'Maior de Idade', maior_idade_entregador )
            
        with col2:
            menor_idade_entregador = df1['Delivery_person_Age'].min()
            col2.metric( 'Menor de Idade', menor_idade_entregador )
            
        with col3:
            melhor_condicao = df1['Vehicle_condition'].max()
            col3.metric( 'Melhor Condição', melhor_condicao )
            
        with col4:
            pior_condicao = df1['Vehicle_condition'].min()
            col4.metric( 'Pior Condição', pior_condicao )

    st.markdown( '''---''' )
    
    with st.container():

        st.markdown( '<h2 style="text-align: center;">Avaliações</h2>', unsafe_allow_html=True )

        col1, col2 = st.columns( 2 )

        with col1:
            st.markdown( '<h5>Avaliação Média por Entregador</h5>', unsafe_allow_html=True )
            avaliacao_media_por_entregador = ( df1.groupby('Delivery_person_ID')['Delivery_person_Ratings']
                                                  .mean()
                                                  .round(2)
                                                  .reset_index() )
            
            st.dataframe( avaliacao_media_por_entregador, height=500 )
            
        with col2:
            st.markdown( '<h5>Avaliação Média por Trânsito</h5>', unsafe_allow_html=True )
            df_aux = ratings_by( df1, 'Road_traffic_density' )
            
            st.dataframe( df_aux )
            
            st.markdown( '<h5>Avaliação Média por Clima</h5>', unsafe_allow_html=True )
            df_aux = ratings_by( df1, 'Weatherconditions' )
            
            st.dataframe( df_aux )

        st.markdown( '''---''' )
    
    with st.container():
        st.markdown( '<h2 style="text-align: center;">Velocidade de Entrega</h2>', unsafe_allow_html=True )
        
        col1, col2 = st.columns( 2 )

        with col1:
            st.markdown( '<h5>Top Entregadores mais Rápidos</h5>', unsafe_allow_html=True )
            df_aux = top_delivers( df1, top_asc=False)
            st.dataframe( df_aux )

        with col2:
            st.markdown( '<h5>Top Entregadores mais Lentos</h5>', unsafe_allow_html=True )
            df_aux = top_delivers( df1, top_asc=True )
            st.dataframe( df_aux )
    
        
with tab2:
    st.title('teste')
with tab3:
    st.title('teste')