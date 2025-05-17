from dash import Dash, dcc, html, Input, Output, no_update
import plotly.express as px
import pandas as pd
import psycopg2
from datetime import datetime

# Configuração do app
app = Dash(__name__)
server = app.server  # Importante para o deployment

# Layout do dashboard
app.layout = html.Div([
    html.H1("Análise de Transporte Público", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    html.Div([
        dcc.Loading(
            id="loading-1",
            type="default",
            children=dcc.Graph(id='map-plot', style={'width': '50%', 'display': 'inline-block'})
        ),
        dcc.Loading(
            id="loading-2",
            type="default",
            children=dcc.Graph(id='passengers-plot', style={'width': '50%', 'display': 'inline-block'})
        )
    ], style={'margin': '20px'}),
    
    html.Div([
        dcc.Loading(
            id="loading-3",
            type="default",
            children=dcc.Graph(id='cluster-plot', style={'width': '50%', 'display': 'inline-block'})
        ),
        dcc.Loading(
            id="loading-4",
            type="default",
            children=dcc.Graph(id='trips-plot', style={'width': '50%', 'display': 'inline-block'})
        )
    ], style={'margin': '20px'}),
    
    dcc.Dropdown(
        id='line-selector',
        placeholder="Selecione uma ou mais linhas",
        multi=True,
        style={'width': '80%', 'margin': '20px auto'}
    ),
    
    html.Div(id='last-update', style={
        'textAlign': 'right',
        'color': '#7f8c8d',
        'fontSize': '12px',
        'margin': '10px'
    })
])

# Callback para carregar as opções do dropdown
@app.callback(
    Output('line-selector', 'options'),
    Input('line-selector', 'value')
)
def update_dropdown_options(_):
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="transport_db",
            user="admin",
            password="password"
        )
        query = "SELECT DISTINCT line FROM transport_data ORDER BY line"
        lines = pd.read_sql(query, conn)['line'].tolist()
        conn.close()
        return [{'label': line, 'value': line} for line in lines]
    except Exception as e:
        print(f"Erro ao carregar linhas: {e}")
        return []

# Callback principal para atualizar todos os gráficos
@app.callback(
    [Output('map-plot', 'figure'),
     Output('passengers-plot', 'figure'),
     Output('cluster-plot', 'figure'),
     Output('trips-plot', 'figure'),
     Output('last-update', 'children')],
    [Input('line-selector', 'value')]
)
def update_all_graphs(selected_lines):
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="transport_db",
            user="admin",
            password="password",
            connect_timeout=5
        )
        
        # Query mais segura
        base_query = """
        SELECT 
            d.line,
            AVG(d.passengers) as avg_passengers,
            COUNT(*) as total_trips,
            AVG(d.lat) as avg_lat,
            AVG(d.lon) as avg_lon,
            c.cluster
        FROM transport_data d
        LEFT JOIN transport_clusters c ON d.id = c.id
        {where_clause}
        GROUP BY d.line, c.cluster
        """
        
        where_clause = "WHERE d.line IN %s" if selected_lines else ""
        params = (tuple(selected_lines),) if selected_lines else ()
        
        query = base_query.format(where_clause=where_clause)
        df = pd.read_sql(query, conn, params=params if selected_lines else None)
        conn.close()
        
        if df.empty:
            empty_fig = px.scatter(title="Sem dados disponíveis").update_layout(plot_bgcolor='white')
            return empty_fig, empty_fig, empty_fig, empty_fig, "Última atualização: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Gráfico 1: Mapa
        map_fig = px.scatter_mapbox(
            df,
            lat="avg_lat",
            lon="avg_lon",
            color="line",
            size="avg_passengers",
            hover_name="line",
            hover_data={
                "avg_passengers": ":.2f",
                "total_trips": True,
                "cluster": True,
                "avg_lat": False,
                "avg_lon": False
            },
            zoom=10,
            height=500
        ).update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0},
            showlegend=False
        )
        
        # Gráfico 2: Passageiros
        passengers_fig = px.bar(
            df,
            x="line",
            y="avg_passengers",
            color="cluster",
            title="Média de Passageiros",
            labels={"avg_passengers": "Passageiros (média)", "line": "Linha"},
            hover_data=["total_trips"]
        ).update_layout(
            xaxis_tickangle=-45,
            plot_bgcolor='white'
        )
        
        # Gráfico 3: Clusters
        cluster_fig = px.pie(
            df,
            names="cluster",
            values="total_trips",
            title="Distribuição por Cluster",
            hole=0.3
        ).update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
        
        # Gráfico 4: Viagens
        trips_fig = px.line(
            df,
            x="line",
            y="total_trips",
            title="Total de Viagens",
            markers=True,
            color="cluster"
        ).update_layout(
            yaxis_title="Número de Viagens",
            xaxis_title="Linha"
        )
        
        return map_fig, passengers_fig, cluster_fig, trips_fig, "Última atualização: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    except Exception as e:
        print(f"Erro ao gerar gráficos: {e}")
        error_fig = px.scatter(title=f"Erro: {str(e)}").update_layout(plot_bgcolor='white')
        return error_fig, error_fig, error_fig, error_fig, "Erro ao atualizar"

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=5000, debug=True)