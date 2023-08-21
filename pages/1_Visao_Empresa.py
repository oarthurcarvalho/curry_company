# BIBLIOTECAS
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

def order_metric( df1 ):
    df_aux = df1.groupby('Order_Date')['ID'].count()
    fig = px.bar(df_aux, x=df_aux.index, y='ID')

    return fig

def traffic_order_share( df1 ):
    df_aux = df1.groupby('Road_traffic_density')['ID'].count()
    df_aux = ((df_aux / df_aux.sum()) * 100).round(2)
    
    fig = px.pie(df_aux, names=df_aux.index, values='ID')

    return fig

def traffic_order_city( df1 ):
            
    df_aux = df1.groupby(['City', 'Road_traffic_density'])['ID'].count()
    df_aux = df_aux.reset_index()

    fig = px.scatter(df_aux, x='City', y='Road_traffic_density', size='ID')
    return fig

def order_by_week( df1 ):
    df_aux = df1.groupby('week_of_year')['ID'].count()
    
    fig = px.line(df_aux, x=df_aux.index, y= 'ID')
    return fig

def order_share_by_week( df1 ):
            
    qnt_entregas_por_semana = df1.groupby( 'week_of_year' )['ID'].count()
    entregadores_unicos_por_semana = df1[['Delivery_person_ID', 'week_of_year' ]].groupby( 'week_of_year' ).nunique()
    
    df_aux = pd.concat([ qnt_entregas_por_semana, entregadores_unicos_por_semana ], axis=1)
    df_aux['order_by_deliver'] = (df_aux['ID'] / df_aux['Delivery_person_ID']).round(2)
    
    fig = px.line(df_aux, x=df_aux.index, y='order_by_deliver')

    return fig

def country_maps( df1 ):
    cols = ['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude']
    df_aux = ( df1[cols].groupby( ['City', 'Road_traffic_density'] )
                        .median()
                        .reset_index()
              )

    map = fl.Map()

    for i in range( len( df_aux ) ):
        fl.Marker( [df_aux.loc[i, 'Delivery_location_latitude'],
                        df_aux.loc[i, 'Delivery_location_longitude']],
                        popup=df_aux.loc[i, 'City'] ).add_to( map )
    
    folium_static( map, width=1024, height=600 )

    return None
#=================================================================================================#
#                            INÍCIO DA ESTRUTURA LÓGICA DO CÓDIGO
#=================================================================================================

#-----------------
# IMPORT DATASET
#-----------------
df = pd.read_csv( 'dataset/train-delivery.csv' )

#---------------------
# LIMPANDO OS DADOS
#---------------------
df1 = clean_data( df )

#-----------------------------
# CONFIGURANDO STREAMLIT PAGE
#-----------------------------
st.set_page_config(
    page_title='Marketplace - Visão Empresa',
    page_icon='img/curry.png', layout='wide'
)

#===========================================================
#                      BARRA LATERAL
#===========================================================
st.header( 'Marketplace - Visão Cliente' )

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

st.sidebar.markdown( """---""" )
st.sidebar.markdown( 'Powered by Comunidade DS' )

# Filtro de data
linhas_selecionadas = df1['Order_Date'] < date_slider
df1 = df1.loc[linhas_selecionadas, : ]

# Filtro de transito
linhas_selecionadas = df1['Road_traffic_density'].isin( traffic_options )
df1 = df1.loc[linhas_selecionadas, : ]


#===========================================================
#                      LAYOUT DASHBOARD
#===========================================================
tab1, tab2, tab3 = st.tabs( ['Visão Gerencial', 'Visão Tática', 'Visão Geográfica'])

###########################################################################################################
#                                             VISÃO GERENCIAL                                             #
###########################################################################################################
with tab1:
    
    #------------------------------------#
    #              Linha 1               #
    #------------------------------------#
    with st.container():
        
        fig = order_metric( df1 )
        st.markdown( '# Orders by Day' )
        st.plotly_chart( fig, use_container_width=True )

    
        
    #------------------------------------#
    #              Linha 2               #
    #------------------------------------#
    with st.container():
        col1, col2 = st.columns( 2 )
        with col1:

            fig = traffic_order_share( df1 )
            st.markdown( '# Traffic Order Share' )
            st.plotly_chart( fig, use_container_width=True )
    
        with col2:
            fig = traffic_order_city( df1 )
            st.markdown( '# Traffic Order City' )
            st.plotly_chart( fig, use_container_width=True )

    

###########################################################################################################
#                                              VISÃO TÁTICA                                               #
###########################################################################################################
with tab2:
    with st.container():
        
        fig = order_by_week( df1 )
        st.markdown('# Order by Week')
        st.plotly_chart( fig, use_container_width=True )

    with st.container():
        fig = order_share_by_week( df1 )
        st.markdown( 'Order Share by Week' )
        st.plotly_chart( fig, use_container_width=True )

###########################################################################################################
#                                            VISÃO GEOGRÁFICA                                             #
###########################################################################################################
with tab3:
    st.markdown('# Country Maps')
    country_maps( df1 )
    


















