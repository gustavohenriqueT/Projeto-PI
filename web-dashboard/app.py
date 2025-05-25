# ... (imports existentes)
from dash import Dash, dcc, html, Input, Output, no_update
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from time import sleep
import warnings

# Filter out pandas SQL warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Configurações do banco de dados
DB_CONFIG = {
    "host": "postgres",
    "database": "transport_db",
    "user": "admin",
    "password": "password",
    "port": "5432"
}

# Create SQLAlchemy engine
# Linha 22 corrigida: Alterado "" para '' na f-string
DB_URL = f'postgresql://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["database"]}'
engine = create_engine(DB_URL)

# Função para verificar conexão com retry
def check_db_connection(max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                # Tenta executar uma consulta simples para verificar a conexão
                conn.execute("SELECT 1").scalar() 
            print("✅ Conexão com PostgreSQL estabelecida")
            return True
        except Exception as e:
            print(f"⚠️ Tentativa {attempt + 1}/{max_retries} - Aguardando PostgreSQL... Erro: {e}")
            sleep(delay)
    # Se todas as tentativas falharem, levanta a exceção
    raise ConnectionError("❌ Falha ao conectar ao PostgreSQL após várias tentativas")


# Inicialização do app
app = Dash(__name__)
server = app.server

# Layout do dashboard
app.layout = html.Div([
    html.Div(id='hidden-div', style={'display': 'none'}),
    dcc.Store(id='database-status', data={'ready': False}),
    dcc.Interval(id='init-timer', interval=5000, n_intervals=0, max_intervals=12),

    html.Div([
        html.H1("Análise de Transporte Público", style={'textAlign': 'center', 'color': '#2c3e50'}),

        html.Div(id='connection-status', style={
            'textAlign': 'center',
            'color': '#e74c3c',
            'padding': '20px'
        }),

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
        ], style={'margin': '20px'}, id='graphs-row-1', hidden=True),

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
        ], style={'margin': '20px'}, id='graphs-row-2', hidden=True),

        dcc.Dropdown(
            id='line-selector',
            placeholder="Selecione uma ou mais linhas",
            multi=True,
            style={'width': '80%', 'margin': '20px auto'},
            disabled=True
        ),

        html.Div(id='last-update', style={
            'textAlign': 'right',
            'color': '#7f8c8d',
            'fontSize': '12px',
            'margin': '10px'
        })
    ], id='main-content', hidden=True)
])

# Callback para verificar conexão inicial
@app.callback(
    [Output('database-status', 'data'),
     Output('connection-status', 'children'),
     Output('main-content', 'hidden'),
     Output('line-selector', 'disabled')],
    Input('init-timer', 'n_intervals')
)
def check_database_connection(n):
    if n == 0: # Para a primeira tentativa, tenta imediatamente.
        print("Tentando conexão inicial com o banco de dados...")

    try:
        if check_db_connection(max_retries=1): # Tenta uma vez por intervalo
            # Verifica se a tabela existe E se tem dados
            with engine.connect() as conn:
                print("Verificando existência e dados da tabela transport_data...")
                # Verifica a existência da tabela
                table_exists = conn.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'transport_data'
                    )
                """).scalar()

                if not table_exists:
                    raise Exception("Tabela 'transport_data' não encontrada!")

                # Verifica se a tabela tem dados
                row_count = conn.execute("SELECT COUNT(*) FROM transport_data").scalar()
                if row_count == 0:
                    raise Exception("Tabela 'transport_data' vazia! Verifique o data-generator e data-warehouse.")

                print(f"Tabela encontrada e contém {row_count} registros. Exibindo conteúdo principal.")
                return {'ready': True}, "", False, False

    except Exception as e:
        print(f"Erro no callback check_database_connection: {e}")
        status_message = f"Conectando ao banco de dados ou verificando tabela... Tentativa {n + 1}/12. Erro: {str(e)}"

        if n >= 11:  # Última tentativa
            status_message = html.Div([
                                html.H3("Erro de conexão com o banco de dados ou tabela não encontrada/vazia"),
                                html.P(str(e)),
                                html.P("Verifique os logs dos contêineres 'postgres', 'data-generator', 'data-warehouse'.")
                            ])

        return (no_update, status_message, True, True)

# Callback para carregar as opções do dropdown
@app.callback(
    Output('line-selector', 'options'),
    Input('database-status', 'data')
)
def update_dropdown_options(db_status):
    if not db_status['ready']:
        return []

    try:
        # Coluna 'linha' em minúsculas
        query = "SELECT DISTINCT linha FROM transport_data ORDER BY linha" 
        lines = pd.read_sql(query, engine)['linha'].tolist()
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
     Output('last-update', 'children'),
     Output('graphs-row-1', 'hidden'),
     Output('graphs-row-2', 'hidden')],
    [Input('line-selector', 'value'),
     Input('database-status', 'data')]
)
def update_all_graphs(selected_lines, db_status):
    if not db_status['ready']:
        return no_update, no_update, no_update, no_update, no_update, True, True

    try:
        base_query = """
        SELECT 
            linha,
            AVG(numero_passageiros) as avg_passengers,
            COUNT(*) as total_trips,
            AVG(latitude) as avg_lat,
            AVG(longitude) as avg_lon,
            horario_pico
        FROM transport_data
        {where_clause}
        GROUP BY linha, horario_pico
        """

        if selected_lines:
            # Usar placeholders corretos para params
            query = base_query.format(where_clause="WHERE linha IN %(lines)s")
            df = pd.read_sql(query, engine, params={'lines': tuple(selected_lines)})
        else:
            query = base_query.format(where_clause="")
            df = pd.read_sql(query, engine)

        if df.empty:
            empty_fig = px.scatter(title="Sem dados disponíveis para seleção").update_layout(plot_bgcolor='white')
            return empty_fig, empty_fig, empty_fig, empty_fig, "Última atualização: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), False, False

        # Gráfico 1: Mapa
        map_fig = px.scatter_mapbox(
            df,
            lat="avg_lat",
            lon="avg_lon",
            color="linha",
            size="avg_passengers",
            hover_name="linha",
            hover_data={
                "avg_passengers": ":.2f",
                "total_trips": True,
                "horario_pico": True,
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
            x="linha",
            y="avg_passengers",
            color="horario_pico",
            title="Média de Passageiros por Linha e Horário de Pico",
            labels={"avg_passengers": "Passageiros (média)", "linha": "Linha", "horario_pico": "Horário de Pico (1=Sim, 0=Não)"},
            hover_data=["total_trips"]
        ).update_layout(
            xaxis_tickangle=-45,
            plot_bgcolor='white'
        )

        # Gráfico 3: Clusters (Horário Pico)
        cluster_fig = px.pie(
            df,
            names="horario_pico",
            values="total_trips",
            title="Distribuição de Viagens por Horário (Pico/Normal)",
            hole=0.3,
            labels={'horario_pico': 'Horário Pico (1=Sim, 0=Não)'}
        ).update_traces(
            textposition='inside',
            textinfo='percent+label'
        )

        # Gráfico 4: Viagens
        trips_fig = px.line(
            df,
            x="linha",
            y="total_trips",
            title="Total de Viagens por Linha e Horário de Pico",
            markers=True,
            color="horario_pico",
            labels={"total_trips": "Número de Viagens", "linha": "Linha", "horario_pico": "Horário de Pico (1=Sim, 0=Não)"}
        ).update_layout(
            yaxis_title="Número de Viagens",
            xaxis_title="Linha"
        )

        # Mostra os gráficos
        return map_fig, passengers_fig, cluster_fig, trips_fig, "Última atualização: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), False, False

    except Exception as e:
        print(f"Erro ao gerar gráficos: {e}")
        error_fig = px.scatter(title=f"Erro ao gerar gráficos: {str(e)}").update_layout(plot_bgcolor='white')
        return error_fig, error_fig, error_fig, error_fig, "Erro ao atualizar: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), False, False

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=5000, debug=False)