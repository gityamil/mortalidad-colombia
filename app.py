import dash
from dash import dcc, html, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Cargar los datos
df_mortalidad = pd.read_excel('data/mortalidad.xlsx')
df_causas = pd.read_excel('data/causas.xlsx')
df_division = pd.read_excel('data/division.xlsx')

# Filtrar solo datos de 2019
df_2019 = df_mortalidad[df_mortalidad['AÑO'] == 2019].copy()

# Preprocesamiento de datos
# Unir con división política para obtener nombres de departamentos/municipios
df_2019 = pd.merge(df_2019, df_division, on=['COD_DANE', 'COD_DEPARTAMENTO', 'COD_MUNICIPIO'], how='left')

# Unir con causas de muerte para obtener descripciones
df_2019 = pd.merge(df_2019, df_causas, left_on='COD_MUERTE', right_on='Código de la CIE-10 cuatro caracteres', how='left')

# Limpiar datos faltantes
df_2019['DEPARTAMENTO'] = df_2019['DEPARTAMENTO'].fillna('Desconocido')
df_2019['MUNICIPIO'] = df_2019['MUNICIPIO'].fillna('Desconocido')
df_2019['Descripcion  de códigos mortalidad a cuatro caracteres'] = df_2019['Descripcion  de códigos mortalidad a cuatro caracteres'].fillna('Causa desconocida')

# Crear aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Layout de la aplicación
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Análisis de Mortalidad en Colombia (2019)", className="text-center mb-4"), width=12)
    ]),
    
    dbc.Tabs([
        # Tab 1: Resumen general
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    html.H3("Distribución de muertes por departamento"),
                    dcc.Graph(id='mapa-mortalidad')
                ], width=6),
                dbc.Col([
                    html.H3("Muertes por mes"),
                    dcc.Graph(id='line-meses')
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H3("Ciudades con mayor mortalidad (homicidios)"),
                    dcc.Graph(id='bar-violentas')
                ], width=6),
                dbc.Col([
                    html.H3("Ciudades con menor mortalidad"),
                    dcc.Graph(id='pie-bajas')
                ], width=6)
            ])
        ], label="Resumen General"),
        
        # Tab 2: Análisis detallado
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    html.H3("Principales causas de muerte"),
                    dash_table.DataTable(
                        id='tabla-causas',
                        columns=[
                            {"name": "Código", "id": "COD_MUERTE"},
                            {"name": "Descripción", "id": "Descripcion  de códigos mortalidad a cuatro caracteres"},
                            {"name": "Total", "id": "count"}
                        ],
                        style_table={'overflowX': 'auto'},
                        page_size=10
                    )
                ], width=6),
                dbc.Col([
                    html.H3("Distribución por edad"),
                    dcc.Graph(id='hist-edades')
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H3("Muertes por sexo y departamento"),
                    dcc.Graph(id='bar-sexo-depto')
                ], width=12)
            ])
        ], label="Análisis Detallado")
    ])
], fluid=True)

# Callbacks para actualizar gráficos

# Mapa de mortalidad por departamento
@app.callback(
    Output('mapa-mortalidad', 'figure'),
    Input('mapa-mortalidad', 'id')
)
def update_mapa(_):
    depto_counts = df_2019.groupby(['COD_DEPARTAMENTO', 'DEPARTAMENTO']).size().reset_index(name='counts')
    
    fig = px.choropleth(
        depto_counts,
        geojson="https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json",
        locations='COD_DEPARTAMENTO',
        color='counts',
        hover_name='DEPARTAMENTO',
        hover_data=['counts'],
        scope='south america',
        color_continuous_scale='Viridis',
        labels={'counts': 'Número de muertes'}
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=400)
    
    return fig

# Gráfico de líneas por mes
@app.callback(
    Output('line-meses', 'figure'),
    Input('line-meses', 'id')
)
def update_line(_):
    meses = df_2019['MES'].value_counts().sort_index().reset_index()
    meses.columns = ['MES', 'count']
    
    fig = px.line(
        meses,
        x='MES',
        y='count',
        title='',
        labels={'MES': 'Mes', 'count': 'Número de muertes'}
    )
    
    fig.update_layout(height=400)
    return fig

# Gráfico de barras ciudades más violentas (homicidios)
@app.callback(
    Output('bar-violentas', 'figure'),
    Input('bar-violentas', 'id')
)
def update_bar_violentas(_):
    # Filtrar homicidios (códigos X95 y otros relacionados con armas de fuego)
    homicidios = df_2019[df_2019['COD_MUERTE'].str.startswith(('X95', 'X96', 'X97', 'X98', 'X99', 'Y00', 'Y01', 'Y02'))]
    
    top_ciudades = homicidios['MUNICIPIO'].value_counts().head(5).reset_index()
    top_ciudades.columns = ['MUNICIPIO', 'count']
    
    fig = px.bar(
        top_ciudades,
        x='MUNICIPIO',
        y='count',
        title='',
        labels={'MUNICIPIO': 'Municipio', 'count': 'Número de homicidios'}
    )
    
    fig.update_layout(height=400)
    return fig

# Gráfico circular ciudades con menor mortalidad
@app.callback(
    Output('pie-bajas', 'figure'),
    Input('pie-bajas', 'id')
)
def update_pie_bajas(_):
    bottom_ciudades = df_2019['MUNICIPIO'].value_counts().tail(10).reset_index()
    bottom_ciudades.columns = ['MUNICIPIO', 'count']
    
    fig = px.pie(
        bottom_ciudades,
        names='MUNICIPIO',
        values='count',
        title='',
        hole=0.4
    )
    
    fig.update_layout(height=400)
    return fig

# Tabla de principales causas de muerte
@app.callback(
    Output('tabla-causas', 'data'),
    Input('tabla-causas', 'id')
)
def update_table(_):
    top_causas = df_2019.groupby(['COD_MUERTE', 'Descripcion  de códigos mortalidad a cuatro caracteres']).size().reset_index(name='count')
    top_causas = top_causas.sort_values('count', ascending=False).head(10)
    return top_causas.to_dict('records')

# Histograma de distribución por edad
@app.callback(
    Output('hist-edades', 'figure'),
    Input('hist-edades', 'id')
)
def update_hist_edades(_):
    # Asumimos que GRUPO_EDAD1 contiene los rangos quinquenales
    fig = px.histogram(
        df_2019,
        x='GRUPO_EDAD1',
        title='',
        labels={'GRUPO_EDAD1': 'Grupo de edad', 'count': 'Número de muertes'}
    )
    
    fig.update_layout(height=400, xaxis={'categoryorder': 'total descending'})
    return fig

# Gráfico de barras apiladas por sexo y departamento
@app.callback(
    Output('bar-sexo-depto', 'figure'),
    Input('bar-sexo-depto', 'id')
)
def update_bar_sexo_depto(_):
    sexo_depto = df_2019.groupby(['DEPARTAMENTO', 'SEXO']).size().reset_index(name='count')
    
    fig = px.bar(
        sexo_depto,
        x='DEPARTAMENTO',
        y='count',
        color='SEXO',
        barmode='stack',
        title='',
        labels={'DEPARTAMENTO': 'Departamento', 'count': 'Número de muertes', 'SEXO': 'Sexo'}
    )
    
    fig.update_layout(height=500)
    return fig

if __name__ == '__main__':
    app.run(debug=True)  # ← NUEVO