# ... (imports existentes)
from dash import Dash, dcc, html, Input, Output, no_update #
import plotly.express as px #
import pandas as pd #
from sqlalchemy import create_engine #
from datetime import datetime #
from time import sleep #
import warnings #

# Filter out pandas SQL warnings
warnings.filterwarnings("ignore", category=UserWarning) #

# Configurações do banco de dados
DB_CONFIG = { #
    "host": "postgres", #
    "database": "transport_db", #
    "user": "admin", #
    "password": "password", #
    "port": "5432" #
}

DB_URL = f'postgresql://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["database"]}' #
engine = create_engine(DB_URL) #

def check_db_connection(max_retries=5, delay=5): #
    for attempt in range(max_retries): #
        try:
            with engine.connect() as conn: #
                conn.execute("SELECT 1").scalar() #
            print("✅ Conexão com PostgreSQL estabelecida") #
            return True #
        except Exception as e:
            print(f"⚠️ Tentativa {attempt + 1}/{max_retries} - Aguardando PostgreSQL... Erro: {e}") #
            sleep(delay) #
    raise ConnectionError("❌ Falha ao conectar ao PostgreSQL após várias tentativas") #

app = Dash(__name__) #
server = app.server #

# Layout do dashboard
app.layout = html.Div([ #
    html.Div(id='hidden-div', style={'display': 'none'}), #
    dcc.Store(id='database-status', data={'ready': False}), #
    dcc.Interval(id='init-timer', interval=3000, n_intervals=0, max_intervals=20), # Aumentado o número de tentativas, intervalo um pouco menor

    html.Div(id='connection-status', style={ # MOVIDO PARA FORA E VISÍVEL
        'textAlign': 'center',
        'color': '#7f8c8d', # Cor neutra inicial
        'padding': '20px',
        'fontSize': '16px',
        'fontWeight': 'bold'
    }, children="Tentando conectar ao servidor e banco de dados..."),

    html.Div([ # Este é o main-content
        html.H1("Análise de Transporte Público", style={'textAlign': 'center', 'color': '#2c3e50'}), #

        # connection-status foi movido para fora do main-content

        html.Div([ #
            dcc.Loading( #
                id="loading-1", #
                type="default", #
                children=dcc.Graph(id='map-plot', style={'width': '50%', 'display': 'inline-block'}) #
            ),
            dcc.Loading( #
                id="loading-2", #
                type="default", #
                children=dcc.Graph(id='passengers-plot', style={'width': '50%', 'display': 'inline-block'}) #
            )
        ], style={'margin': '20px'}, id='graphs-row-1', hidden=True), #

        html.Div([ #
            dcc.Loading( #
                id="loading-3", #
                type="default", #
                children=dcc.Graph(id='cluster-plot', style={'width': '50%', 'display': 'inline-block'}) #
            ),
            dcc.Loading( #
                id="loading-4", #
                type="default", #
                children=dcc.Graph(id='trips-plot', style={'width': '50%', 'display': 'inline-block'}) #
            )
        ], style={'margin': '20px'}, id='graphs-row-2', hidden=True), #

        dcc.Dropdown( #
            id='line-selector', #
            placeholder="Selecione uma ou mais linhas", #
            multi=True, #
            style={'width': '80%', 'margin': '20px auto'}, #
            disabled=True #
        ),

        html.Div(id='last-update', style={ #
            'textAlign': 'right',
            'color': '#7f8c8d',
            'fontSize': '12px',
            'margin': '10px'
        })
    ], id='main-content', hidden=True) #
])

# Callback para verificar conexão inicial
@app.callback( #
    [Output('database-status', 'data'), #
     Output('connection-status', 'children'), # Atualizado para o novo Div de status
     Output('connection-status', 'style'), # Para mudar a cor do status
     Output('main-content', 'hidden'), #
     Output('line-selector', 'disabled')], #
    Input('init-timer', 'n_intervals') #
)
def check_database_connection(n): #
    base_style = {'textAlign': 'center', 'padding': '20px', 'fontSize': '16px', 'fontWeight': 'bold'}
    if n == 0: #
        print("Tentando conexão inicial com o banco de dados...") #

    try:
        if check_db_connection(max_retries=1, delay=2): # Tenta uma vez por intervalo, delay curto #
            with engine.connect() as conn: #
                print("Verificando existência e dados da tabela transport_data...") #
                table_exists = conn.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'transport_data'
                    )
                """).scalar() #

                if not table_exists: #
                    raise Exception("Tabela 'transport_data' não encontrada!") #

                row_count = conn.execute("SELECT COUNT(*) FROM transport_data").scalar() #
                if row_count == 0: #
                    # Não é mais um erro fatal aqui, apenas um aviso, pois o data-warehouse pode estar em processo
                    print("Tabela 'transport_data' está vazia! Aguardando dados do data-warehouse...") #
                    status_message = f"⚠️ Tabela 'transport_data' vazia. Aguardando dados... Tentativa {n + 1}/20"
                    status_style = {**base_style, 'color': '#f39c12'} # Amarelo para tabela vazia
                    return {'ready': False}, status_message, status_style, True, True

                print(f"Tabela encontrada e contém {row_count} registros. Exibindo conteúdo principal.") #
                status_message = f"✅ Conectado ao banco de dados. Tabela 'transport_data' com {row_count} registros."
                status_style = {**base_style, 'color': '#2ecc71'} # Verde para sucesso
                return {'ready': True}, status_message, status_style, False, False #

    except Exception as e: #
        print(f"Erro no callback check_database_connection (tentativa {n+1}): {e}") #
        status_message = f"⚠️ Conectando ao BD ou verificando tabela... Tentativa {n + 1}/20. Erro: {str(e)}" #
        status_style = {**base_style, 'color': '#e67e22'} # Laranja para aviso/tentativa

        if n >= 19:  # Última tentativa (max_intervals - 1) #
            status_message = html.Div([ #
                                html.H3("❌ Erro: Falha ao conectar ao banco de dados ou tabela 'transport_data' não populada."), #
                                html.P(f"Último erro: {str(e)}"), #
                                html.P("Verifique os logs dos contêineres 'postgres', 'data-generator', 'r-processing' e 'data-warehouse'.") #
                            ])
            status_style = {**base_style, 'color': '#e74c3c'} # Vermelho para erro final
        return no_update, status_message, status_style, True, True #


@app.callback( #
    Output('line-selector', 'options'), #
    Input('database-status', 'data') #
)
def update_dropdown_options(db_status): #
    if not db_status or not db_status.get('ready'): # Adicionado get para segurança #
        return [] #
    try:
        query = "SELECT DISTINCT linha FROM transport_data ORDER BY linha" #
        lines_df = pd.read_sql(query, engine) #
        if lines_df.empty:
            return []
        return [{'label': str(line), 'value': str(line)} for line in lines_df['linha'].tolist()] # Adicionado str() para segurança
    except Exception as e:
        print(f"Erro ao carregar linhas para dropdown: {e}") #
        return [] #

@app.callback( #
    [Output('map-plot', 'figure'), #
     Output('passengers-plot', 'figure'), #
     Output('cluster-plot', 'figure'), #
     Output('trips-plot', 'figure'), #
     Output('last-update', 'children'), #
     Output('graphs-row-1', 'hidden'), #
     Output('graphs-row-2', 'hidden')], #
    [Input('line-selector', 'value'), #
     Input('database-status', 'data')] #
)
def update_all_graphs(selected_lines, db_status): #
    if not db_status or not db_status.get('ready'): # Verificação mais robusta #
        return no_update, no_update, no_update, no_update, no_update, True, True #

    try:
        base_query = """
        SELECT 
            linha,
            AVG(numero_passageiros) as avg_passengers,
            COUNT(*) as total_trips,
            AVG(latitude) as avg_lat,
            AVG(longitude) as avg_lon,
            CAST(horario_pico AS INTEGER) as horario_pico_int -- Usado para agrupar e colorir
        FROM transport_data
        {where_clause}
        GROUP BY linha, horario_pico -- Agrupar pelo booleano original ou o int casteado
        ORDER BY linha, horario_pico_int
        """ #

        params = {}
        if selected_lines: #
            query = base_query.format(where_clause="WHERE linha IN %(lines)s") #
            params = {'lines': tuple(selected_lines)} #
        else:
            query = base_query.format(where_clause="") #
        
        df = pd.read_sql(query, engine, params=params) #

        if df.empty: #
            empty_fig = px.scatter(title="Sem dados disponíveis para a seleção atual.").update_layout(
                plot_bgcolor='white', paper_bgcolor='white',
                xaxis={'visible': False}, yaxis={'visible': False}
            ) #
            return empty_fig, empty_fig, empty_fig, empty_fig, "Última atualização: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), False, False #

        # Prepara descrições para legendas
        df['horario_pico_desc'] = df['horario_pico_int'].apply(lambda x: 'Pico (Sim)' if x == 1 else 'Pico (Não)')

        map_fig = px.scatter_mapbox( #
            df, lat="avg_lat", lon="avg_lon", color="linha", size="avg_passengers", #
            hover_name="linha", hover_data={"avg_passengers": ":.2f", "total_trips": True, "horario_pico_desc": True, "avg_lat":False, "avg_lon":False}, #
            zoom=10, height=500, title="Localização Média e Volume de Passageiros por Linha" #
        ).update_layout(mapbox_style="open-street-map", margin={"r":0,"t":35,"l":0,"b":0}, showlegend=True, paper_bgcolor='white') #

        passengers_fig = px.bar( #
            df, x="linha", y="avg_passengers", color="horario_pico_desc", #
            title="Média de Passageiros por Linha e Horário de Pico", #
            labels={"avg_passengers": "Passageiros (média)", "linha": "Linha", "horario_pico_desc": "Horário de Pico"}, #
            hover_data=["total_trips"], barmode='group' #
        ).update_layout(xaxis_tickangle=-45, plot_bgcolor='white', paper_bgcolor='white', legend_title_text='Horário de Pico') #
        
        # Para o gráfico de pizza, precisamos agregar os total_trips por horario_pico_desc
        df_pie = df.groupby("horario_pico_desc")["total_trips"].sum().reset_index()

        cluster_fig = px.pie( #
            df_pie, names="horario_pico_desc", values="total_trips", #
            title="Distribuição de Viagens por Horário (Pico/Normal)", hole=0.3, #
            labels={'horario_pico_desc': 'Horário de Pico'} #
        ).update_traces(textposition='inside', textinfo='percent+label').update_layout(paper_bgcolor='white') #

        trips_fig = px.line( #
            df, x="linha", y="total_trips", title="Total de Viagens por Linha e Horário de Pico", #
            markers=True, color="horario_pico_desc", #
            labels={"total_trips": "Número de Viagens", "linha": "Linha", "horario_pico_desc": "Horário de Pico"} #
        ).update_layout(yaxis_title="Número de Viagens", xaxis_title="Linha", paper_bgcolor='white', plot_bgcolor='white', legend_title_text='Horário de Pico') #

        return map_fig, passengers_fig, cluster_fig, trips_fig, "Última atualização: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), False, False #

    except Exception as e:
        print(f"Erro ao gerar gráficos: {e}") #
        error_fig = px.scatter(title=f"Erro ao gerar gráficos: {str(e)}").update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis={'visible': False}, yaxis={'visible': False}
        ) #
        return error_fig, error_fig, error_fig, error_fig, "Erro ao atualizar: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), False, False #

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=5000, debug=True) # MUDADO PARA debug=True