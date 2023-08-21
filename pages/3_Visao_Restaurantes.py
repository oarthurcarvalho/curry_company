import pandas as pd
import numpy as np
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
    df1 = df1[(df1['City'].notna()) & (df1['Festival'].notna()) & (df1['Road_traffic_density'].notna()) & (df1['Weatherconditions'].notna())]
    
    ## 2. Eliminando os espaços vazios ao final dos valores.
    cols_to_strip = ['ID', 'Delivery_person_ID', 'Road_traffic_density', 'Type_of_order', 'Type_of_vehicle', 'Festival', 'City']
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
    
def generate_point_id(row):
    return hash((row['Restaurant_latitude'], row['Restaurant_longitude']))

def distance( df1 ):
    cols = ['Restaurant_latitude', 'Restaurant_longitude',
            'Delivery_location_latitude', 'Delivery_location_longitude']

    df1['distance'] = df1.loc[:, cols].apply( lambda x:
                                             haversine(
                                                 (x['Restaurant_latitude'],
                                                  x['Restaurant_longitude']),
                                                 (x['Delivery_location_latitude'],
                                                  x['Delivery_location_longitude']) ), axis=1 )
    
    avg_distance = df1['distance'].mean().round(2)

    return avg_distance

def avg_time_delivery( df1, op, festival ):

    """
        Esta função calcula o tempo médio e o desvio padrão do tempo de entrega.
        Parâmetros:
            Input:
                - df: Dataframe com os dados necessários para o cálculo
                - op: Tipo de operação que precisa ser calculado
                    'avg_time': Calcula o tempo médio
                    'std_time': Calcula o desvio padrão do tempo.
            Output:
                - df: Dataframe com 2 colunas e 1 linha.
    """
    
    cols = ['Time_taken(min)', 'Festival']
    df_aux = df1.loc[:, cols].groupby( 'Festival' ).agg( {'Time_taken(min)': ['mean', 'std']} )
    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()
    
    linhas_selecionadas = df_aux['Festival'] == festival
    df_aux = df_aux.loc[linhas_selecionadas, op].round(2)
    
    return df_aux

def avg_delivery_city( df1 ):
    cols = ['City', 'Time_taken(min)']
    df_aux = df1.loc[:, ].groupby( 'City' ).agg( {'Time_taken(min)': ['mean', 'std']} )
    
    df_aux.columns = ['avg_time', 'std_time']
    
    df_aux = df_aux.reset_index()
    
    fig = go.Figure()
    fig.add_trace( go.Bar( name='Control',
                         x=df_aux['City'],
                         y=df_aux['avg_time'],
                         error_y=dict( type='data', array=df_aux['std_time'])
                         )
                 )

    return fig

def time_distribute( df1 ):
    cols = [
        'Restaurant_latitude', 'Restaurant_longitude',
        'Delivery_location_latitude', 'Delivery_location_longitude'
    ]

    df1['distance'] = ( df1.loc[:, cols]
                           .apply( lambda x: haversine(
                               (
                                   x['Restaurant_latitude'],
                                   x['Restaurant_longitude']
                               ),
                               (
                                   x['Delivery_location_latitude'],
                                   x['Delivery_location_longitude']
                               )
                        ), axis=1 ) )
    
    avg_distance = df1.groupby( 'City' )['distance'].mean().reset_index().round(2)
    
    fig = go.Figure(
        data=[
            go.Pie(
                labels=avg_distance['City'],
                values=avg_distance['distance'],
                pull=[0, 0.1, 0]
            )
        ]
    )
    return fig

def sunburst_chart( df1 ):
    cols = ['City', 'Time_taken(min)', 'Road_traffic_density']
    df_aux = ( df1.loc[:, cols]
                  .groupby( ['City', 'Road_traffic_density'] )
                  .agg( {'Time_taken(min)': ['mean', 'std']} ) 
             )
    
    df_aux.columns = ['avg_time', 'std_time']
    
    df_aux = df_aux.reset_index()
    
    fig = px.sunburst(df_aux, path=['City', 'Road_traffic_density'],
                      values='avg_time', color='std_time', color_continuous_scale='RdBu',
                      color_continuous_midpoint=np.average(df_aux['std_time'])
                     )
    return fig

def avg_distance_restaurant( df1 ):
                
    df1['Restaurant_ID'] = df1.apply(generate_point_id, axis=1).abs()
    mean_count_distance_ratings = ( 
        df1.groupby('Restaurant_ID')[['distance', 'Delivery_person_Ratings']]
           .agg({'distance': ['mean', 'count'], 'Delivery_person_Ratings': 'mean'})
           .sort_values(by=('distance', 'mean'))
           .reset_index()
    )
    
    mean_count_distance_ratings.columns = [
        'Restaurant_ID', 'distance_mean', 'distance_count', 'ratings_mean'
    ]
    return mean_count_distance_ratings
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
st.set_page_config(page_title='Marketplace - Visão Restaurante', page_icon='img/curry.png', layout='wide')

#===========================================================
#                      BARRA LATERAL
#===========================================================
st.header( 'Marketplace - Visão Restaurantes' )

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
    st.markdown( '# Overral Metrics' )

    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns( 6 )
    
        with col1:
            qnt_entregadores_unicos = df['Delivery_person_ID'].nunique()

            col1.metric( 'Entregadores Únicos', qnt_entregadores_unicos )
        with col2:
            avg_distance = distance( df1 )
            col2.metric( 'Distância Média', avg_distance )
            
        with col3:
            df_aux = avg_time_delivery( df1, 'avg_time', 'Yes')
            col3.metric( 'Tempo Médio de Entrega c/ Festival', df_aux )
            
        with col4:
            df_aux = avg_time_delivery( df1, 'std_time', 'Yes')
            col4.metric( 'Std de Entrega c/ Festival', df_aux )
            
        with col5:
            df_aux = avg_time_delivery( df1, 'avg_time', 'No')
            col5.metric( 'Tempo Médio s/ Festival', df_aux )
        with col6:
            df_aux = avg_time_delivery( df1, 'std_time', 'No')
            col6.metric( 'Std de Entrega s/ Festival', df_aux )

    
    with st.container():

        col1, col2 = st.columns( 2 )

        with col1:

            st.markdown( 'Tempo Médio de entrega por cidade' )
            fig = avg_delivery_city( df1 )
            col1.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown( 'Média de distancia do restaurantes' )
            mean_count_distance_ratings = avg_distance_restaurant( df1 )
            col2.dataframe( mean_count_distance_ratings )
            

    with st.container():
        st.markdown( 'Distribuição do Tempo' )

        col1, col2 = st.columns( 2 )
        
        with col1:

            time_distribute( df1 )
            col1.plotly_chart( fig, use_container_width=True )

        with col2:
            fig = sunburst_chart( df1 )
            col2.plotly_chart( fig, use_container_width=True )
        
with tab2:
    st.markdown(' # Teste 2' )
with tab3:
    st.markdown(' # Teste 3' )











