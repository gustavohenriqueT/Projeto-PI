from dash import Dash, dcc, html, Input, Output, no_update
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine, text # Adicionado text
from datetime import datetime
from time import sleep
import warnings
import os 
import base64 
import json 

# Filter out pandas SQL warningsFyan
warnings.filterwarnings("ignore", category=UserWarning)

# Configurações do banco de dados
DB_CONFIG = {
    "host": "postgres",
    "database": "transport_db",
    "user": "admin",
    "password": "password",
    "port": "5432"
}

DB_URL = f'postgresql://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["database"]}'
engine = create_engine(DB_URL) 

def check_db_connection(max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1")).scalar() # Usando text()
            print("✅ Conexão com PostgreSQL estabelecida")
            return True
        except Exception as e:
            print(f"⚠️ Tentativa {attempt + 1}/{max_retries} - Aguardando PostgreSQL... Erro: {e}")
            sleep(delay)
    raise ConnectionError("❌ Falha ao conectar ao PostgreSQL após várias tentativas")

app = Dash(__name__)
server = app.server

# Layout do dashboard
app.layout = html.Div([
    html.Div(id='hidden-div', style={'display': 'none'}),
    dcc.Store(id='database-status', data={'ready': False}),
    dcc.Interval(id='init-timer', interval=3000, n_intervals=0, max_intervals=20, disabled=False),

    html.Div(id='connection-status', style={
        'textAlign': 'center',
        'color': '#7f8c8d', 
        'padding': '20px',
        'fontSize': '16px',
        'fontWeight': 'bold'
    }, children="Tentando conectar ao servidor e banco de dados..."),

    html.Div([ # Este é o main-content
        html.H1("Análise de Transporte Público", style={'textAlign': 'center', 'color': '#2c3e50'}),

        dcc.Dropdown(
            id='line-selector',
            placeholder="Selecione uma ou mais linhas (afeta gráficos abaixo)",
            multi=True,
            style={'width': '80%', 'margin': '20px auto', 'marginBottom': '30px'},
            disabled=True
        ),

        html.Div([
            dcc.Loading(children=dcc.Graph(id='map-plot'), id="loading-map"),
            dcc.Loading(children=dcc.Graph(id='passengers-plot'), id="loading-passengers")
        ], style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'space-around', 'margin': '10px'}, id='graphs-row-1', hidden=True),

        html.Div([
            dcc.Loading(children=dcc.Graph(id='cluster-plot'), id="loading-cluster-plot"), 
            dcc.Loading(children=dcc.Graph(id='trips-plot'), id="loading-trips")
        ], style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'space-around', 'margin': '10px'}, id='graphs-row-2', hidden=True),
        
        html.Div([ 
            dcc.Loading(children=dcc.Graph(id='trip-time-plot'), id="loading-trip-time")
        ], style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'space-around', 'margin': '10px'}, id='graphs-row-3', hidden=True),
        
        html.Div(id='olap-section', hidden=True, children=[
            html.H2("Análise OLAP: Tempo Médio de Viagem", style={'textAlign': 'center', 'marginTop': '30px'}),
            html.Div([
                dcc.Dropdown(id='olap-dim1-dropdown', options=[{'label': 'Linha', 'value': 'linha'}, {'label': 'Hora do Dia', 'value': 'hora'}, {'label': 'Horário de Pico (Sim/Não)', 'value': 'horario_pico_desc'}], value='linha', clearable=False, style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
                dcc.Dropdown(id='olap-dim2-dropdown', options=[{'label': 'Nenhuma (Agrupar por 1 Dimensão)', 'value': 'Nenhuma'},{'label': 'Linha', 'value': 'linha'}, {'label': 'Hora do Dia', 'value': 'hora'}, {'label': 'Horário de Pico (Sim/Não)', 'value': 'horario_pico_desc'}], value='horario_pico_desc', clearable=False, style={'width': '48%', 'display': 'inline-block'})
            ], style={'width': '80%', 'margin': '15px auto'}),
            dcc.Loading(id="loading-olap", children=dcc.Graph(id='olap-interactive-plot'))
        ], style={'margin': '20px', 'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'backgroundColor': '#f9f9f9'}),
        
        html.Div(id='ml-results-section', hidden=True, children=[
            html.H2("Resultados de Machine Learning e Clusterização", style={'textAlign': 'center', 'marginTop': '30px'}),
            html.Div([ 
                html.Div([ 
                    html.H3("Modelo de Classificação (Horário de Pico)", style={'textAlign': 'center'}),
                    dcc.Loading(id="loading-ml-metrics", children=html.Div(id='ml-metrics-display', style={'padding': '10px', 'border': '1px solid #eee', 'borderRadius': '5px', 'marginBottom': '20px', 'backgroundColor': 'white'})),
                    html.H4("Importância das Features (Classificação)", style={'textAlign': 'center'}),
                    dcc.Loading(id="loading-feature-importance", children=html.Img(id='feature-importance-img', style={'maxWidth': '100%', 'maxHeight':'350px', 'height': 'auto', 'display': 'block', 'margin': 'auto'}))
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '2%', 'padding': '10px', 'boxSizing': 'border-box'}),
                html.Div([ 
                    html.H3("Análise de Clusterização (HDBSCAN)", style={'textAlign': 'center'}),
                    dcc.Loading(id="loading-clustering-metrics", children=html.Div(id='clustering-metrics-display', style={'padding': '10px', 'border': '1px solid #eee', 'borderRadius': '5px', 'marginBottom': '20px', 'backgroundColor': 'white'})),
                    html.H4("Visualização dos Clusters (PCA)", style={'textAlign': 'center'}),
                    dcc.Loading(id="loading-clustering-pca", children=html.Img(id='clustering-pca-img', style={'maxWidth': '100%', 'maxHeight':'350px', 'height': 'auto', 'display': 'block', 'margin': 'auto'}))
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '10px', 'boxSizing': 'border-box'})
            ], style={'display': 'flex', 'justify-content': 'space-between', 'flexWrap': 'wrap'})
        ], style={'margin': '20px', 'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'backgroundColor': '#f9f9f9'}),

        html.Div(id='last-update', style={'textAlign': 'right', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '10px'})
    ], id='main-content', hidden=True)
])

# --- Callbacks ---
@app.callback(
    [Output('database-status', 'data'),
     Output('connection-status', 'children'), Output('connection-status', 'style'),
     Output('main-content', 'hidden'), Output('line-selector', 'disabled'),
     Output('init-timer', 'disabled'), Output('olap-section', 'hidden'),
     Output('ml-results-section', 'hidden')],
    Input('init-timer', 'n_intervals')
)
def check_database_connection(n):
    base_style = {'textAlign': 'center', 'padding': '20px', 'fontSize': '16px', 'fontWeight': 'bold'}
    timer_disabled, olap_hidden, ml_hidden = False, True, True 
    status_msg = "Tentando conectar..."
    status_style = {**base_style, 'color': '#7f8c8d'}

    if n == 0: print("Tentando conexão inicial com o banco de dados...")

    try:
        if check_db_connection(max_retries=1, delay=1):
            with engine.connect() as conn:
                table_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'transport_data')")).scalar() # Usando text()
                if not table_exists: raise Exception("Tabela 'transport_data' não encontrada!")
                row_count = conn.execute(text("SELECT COUNT(*) FROM transport_data")).scalar() # Usando text()
                if row_count == 0:
                    status_msg = f"⚠️ Tabela 'transport_data' vazia. Aguardando dados... Tentativa {n + 1}/20"
                    status_style['color'] = '#f39c12'
                    return {'ready': False}, status_msg, status_style, True, True, timer_disabled, olap_hidden, ml_hidden
                
                status_msg = f"✅ Conectado. Tabela 'transport_data' com {row_count} registros."
                status_style['color'] = '#2ecc71'
                timer_disabled, olap_hidden, ml_hidden = True, False, False 
                return {'ready': True}, status_msg, status_style, False, False, timer_disabled, olap_hidden, ml_hidden
    except Exception as e:
        error_text = str(e)
        print(f"Erro check_db_connection (tentativa {n+1}): {error_text}")
        status_msg = f"⚠️ Conectando/Verificando Tabela... Tentativa {n + 1}/20. Erro: {error_text}"
        status_style['color'] = '#e67e22'
        if n >= 19:
            status_msg_content = [
                html.H3("❌ Erro Final: Falha na conexão/verificação da tabela."),
                html.P(f"Último erro: {error_text}"),
                html.P("Verifique logs: postgres, data-generator, r-processing, data-warehouse, spark-submit-job, clustering-analysis.")
            ]
            status_msg = html.Div(status_msg_content) 
            status_style['color'] = '#e74c3c'
            timer_disabled = True
    return no_update, status_msg, status_style, True, True, timer_disabled, olap_hidden, ml_hidden

@app.callback(Output('line-selector', 'options'), Input('database-status', 'data'))
def update_dropdown_options(db_status):
    if not db_status or not db_status.get('ready'): return []
    try:
        query = text("SELECT DISTINCT linha FROM transport_data ORDER BY linha") # Usando text()
        df_lines = pd.read_sql(query, engine)
        return [{'label': str(l), 'value': str(l)} for l in df_lines['linha']] if not df_lines.empty else []
    except Exception as e:
        print(f"Erro ao carregar linhas para dropdown: {e}"); return []

@app.callback(
    [Output('map-plot', 'figure'), Output('passengers-plot', 'figure'),
     Output('cluster-plot', 'figure'), Output('trips-plot', 'figure'),
     Output('trip-time-plot', 'figure'), Output('last-update', 'children'),
     Output('graphs-row-1', 'hidden'), Output('graphs-row-2', 'hidden'), Output('graphs-row-3', 'hidden')],
    [Input('line-selector', 'value'), Input('database-status', 'data')]
)
def update_all_graphs(selected_lines, db_status):
    if not db_status or not db_status.get('ready'):
        return (no_update,) * 5 + (no_update,) + (True,) * 3 

    fig_layout_defaults = {'plot_bgcolor': 'white', 'paper_bgcolor': 'white'}
    empty_fig_placeholder_layout = {**fig_layout_defaults, 'xaxis': {'visible': False}, 'yaxis': {'visible': False}}
    
    title_sem_dados = "Sem dados disponíveis para a seleção atual."
    title_erro_graficos = "Ocorreu um erro ao gerar os gráficos."

    try:
        base_query_str = """SELECT linha, AVG(numero_passageiros) as avg_passengers, COUNT(*) as total_trips,
                        AVG(latitude) as avg_lat, AVG(longitude) as avg_lon,
                        CAST(horario_pico AS INTEGER) as horario_pico_int, AVG(tempo_viagem_minutos) as avg_trip_time 
                        FROM transport_data {where_clause} GROUP BY linha, horario_pico ORDER BY linha, horario_pico_int"""
        
        params = {}
        if selected_lines:
            final_query_str = base_query_str.format(where_clause="WHERE linha IN :lines") 
            params = {'lines': tuple(selected_lines)}
        else:
            final_query_str = base_query_str.format(where_clause="")
        
        df = pd.read_sql(text(final_query_str), engine, params=params) 

        if df.empty:
            fig = px.scatter(title=title_sem_dados).update_layout(**empty_fig_placeholder_layout)
            return (fig,) * 5 + ("Atualizado: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), False, False, False)

        df['horario_pico_desc'] = df['horario_pico_int'].apply(lambda x: 'Pico (Sim)' if x == 1 else 'Pico (Não)')
        
        map_fig = px.scatter_mapbox(df, lat="avg_lat", lon="avg_lon", color="linha", size="avg_passengers", hover_name="linha", 
                                    hover_data={"avg_passengers": ":.2f", "total_trips": True, "horario_pico_desc": True, "avg_lat":False, "avg_lon":False},
                                    zoom=10, height=500, title="Localização Média e Volume de Passageiros"
                                   ).update_layout(mapbox_style="open-street-map", margin={"r":0,"t":35,"l":0,"b":0}, showlegend=True, **fig_layout_defaults)  # type: ignore
        
        pass_fig = px.bar(df, x="linha", y="avg_passengers", color="horario_pico_desc", title="Média de Passageiros", 
                          labels={"avg_passengers": "Média de Passageiros", "horario_pico_desc": "Pico?"}, barmode='group'
                         ).update_layout(xaxis_tickangle=-45, legend_title_text='Horário Pico', **fig_layout_defaults) # type: ignore
        
        df_pie = df.groupby("horario_pico_desc")["total_trips"].sum().reset_index()
        clu_fig = px.pie(df_pie, names="horario_pico_desc", values="total_trips", title="Viagens em Pico/Não Pico", 
                         hole=0.3, labels={'horario_pico_desc': 'Pico?'}
                        ).update_traces(textposition='inside', textinfo='percent+label').update_layout(**fig_layout_defaults) # type: ignore
        
        trip_fig_ln = px.line(df, x="linha", y="total_trips", color="horario_pico_desc", markers=True, title="Total de Viagens por Linha", 
                              labels={"total_trips": "Nº Viagens", "horario_pico_desc": "Pico?"}
                             ).update_layout(legend_title_text='Horário Pico', **fig_layout_defaults) # type: ignore
        
        trip_time_bar = px.bar(df, x="linha", y="avg_trip_time", color="horario_pico_desc", title="Tempo Médio de Viagem (min)", 
                               labels={"avg_trip_time": "Tempo Médio (min)", "horario_pico_desc": "Pico?"}, barmode='group'
                              ).update_layout(xaxis_tickangle=-45, legend_title_text='Horário Pico', **fig_layout_defaults) # type: ignore
         
        return map_fig, pass_fig, clu_fig, trip_fig_ln, trip_time_bar, "Atualizado: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), False, False, False
    except Exception as e:
        print(f"Erro ao gerar gráficos principais: {e}")
        fig = px.scatter(title=title_erro_graficos).update_layout(**empty_fig_placeholder_layout)
        return (fig,) * 5 + ("Erro ao atualizar", False, False, False)

@app.callback(Output('olap-interactive-plot', 'figure'),
    [Input('olap-dim1-dropdown', 'value'), Input('olap-dim2-dropdown', 'value'), Input('database-status', 'data')])
def update_olap_plot(dim1_key, dim2_key, db_status):
    fig_layout_defaults = {'plot_bgcolor': 'white', 'paper_bgcolor': 'white'}
    empty_fig_placeholder_layout = {**fig_layout_defaults, 'xaxis': {'visible': False}, 'yaxis': {'visible': False}}
    
    if not db_status or not db_status.get('ready'):
        return px.scatter(title="Aguardando dados para OLAP...").update_layout(**empty_fig_placeholder_layout)

    dim_sql_map = {'linha': 'linha', 'hora': 'CAST(hora AS TEXT)', 'horario_pico_desc': "CASE WHEN horario_pico THEN 'Pico (Sim)' ELSE 'Pico (Não)' END"}
    metric_agg, agg_func = 'tempo_viagem_minutos', 'AVG'
    dim1_sql, dim1_label = (dim_sql_map.get(dim1_key, dim_sql_map['linha']), dim1_key if dim1_key in dim_sql_map else 'linha')
    
    select_expr, groupby_expr = [f"{dim1_sql} AS dim1"], [f"{dim1_sql}"]
    dim2_alias, dim2_label = None, None
    if dim2_key != 'Nenhuma' and dim2_key in dim_sql_map and dim2_key != dim1_key:
        dim2_sql = dim_sql_map[dim2_key]
        dim2_alias, dim2_label = 'dim2', dim2_key
        select_expr.append(f"{dim2_sql} AS {dim2_alias}")
        groupby_expr.append(f"{dim2_sql}")

    query_olap_str = f"SELECT {', '.join(select_expr)}, {agg_func}({metric_agg}) AS metric_val FROM transport_data GROUP BY {', '.join(groupby_expr)} ORDER BY {', '.join(groupby_expr)}, metric_val DESC NULLS LAST"
    
    try:
        df_res = pd.read_sql_query(text(query_olap_str), engine) # Usando text()
        if df_res.empty: return px.scatter(title="Sem dados para esta combinação OLAP.").update_layout(**empty_fig_placeholder_layout)
        
        title_str = f'{agg_func.capitalize()} de {metric_agg.replace("_"," ")} por {dim1_label.replace("_"," ").capitalize()}'
        labels = {'dim1': dim1_label.replace("_"," ").capitalize(), 'metric_val': f'{agg_func.capitalize()} {metric_agg.replace("_"," ")}'}
        legend_title = ""
        if dim2_alias:
            title_str += f' e {dim2_label.replace("_"," ").capitalize()}' # type: ignore
            labels['dim2'] = dim2_label.replace("_"," ").capitalize() # type: ignore
            legend_title = dim2_label.replace("_"," ").capitalize() # type: ignore
        
        fig = px.bar(df_res, x='dim1', y='metric_val', color='dim2' if dim2_alias else None, barmode='group' if dim2_alias else 'relative', title=title_str, labels=labels)
        fig.update_layout(xaxis_tickangle=-45, legend_title_text=legend_title, xaxis_title=dim1_label.replace("_"," ").capitalize(), **fig_layout_defaults) # Usando fig_layout_defaults # type: ignore
        return fig
    except Exception as e:
        print(f"Erro na consulta OLAP: {e}")
        return px.scatter(title="Ocorreu um erro ao gerar o gráfico OLAP.").update_layout(**empty_fig_placeholder_layout)

@app.callback(
    [Output('ml-metrics-display', 'children'), Output('feature-importance-img', 'src'),
     Output('clustering-metrics-display', 'children'), Output('clustering-pca-img', 'src')],
    Input('database-status', 'data')
)
def update_analysis_results(db_status):
    if not db_status or not db_status.get('ready'):
        return "Aguardando resultados de ML...", "", "Aguardando resultados de Clusterização...", ""

    ml_metrics_path = "/app/shared_data/ml_classification_metrics.json"
    feature_img_path = "/app/shared_data/feature_importances.png"
    clustering_metrics_path = "/app/shared_data/clustering_metrics.json"
    pca_img_path = "/app/shared_data/hdbscan_clusters_pca.png"

    ml_metrics_children, feature_img_src = [], ""
    try:
        if os.path.exists(ml_metrics_path):
            with open(ml_metrics_path, 'r') as f: metrics = json.load(f)
            ml_metrics_children.append(html.H4("Métricas de Classificação:"))
            ul_items = [html.Li(f"{k.replace('_',' ').capitalize()}: {v:.2%}" if isinstance(v, float) and 0<=v<=1 and v is not None else f"{k.replace('_',' ').capitalize()}: {str(v)}") for k,v in metrics.items()] # Adicionado str(v) e checagem de None
            ml_metrics_children.append(html.Ul(ul_items))
        else: ml_metrics_children.append(html.P("Métricas de classificação (ml_classification_metrics.json) não encontradas."))
    except Exception as e:
        print(f"Erro ao carregar métricas de classificação: {e}"); ml_metrics_children.append(html.P(f"Erro ao carregar métricas de classificação: {str(e)}"))

    try:
        if os.path.exists(feature_img_path):
            encoded_image = base64.b64encode(open(feature_img_path, 'rb').read())
            feature_img_src = f'data:image/png;base64,{encoded_image.decode()}'
    except Exception as e: print(f"Erro ao carregar imagem de importância das features: {e}")

    clustering_metrics_children, pca_img_src = [], ""
    try:
        if os.path.exists(clustering_metrics_path):
            with open(clustering_metrics_path, 'r') as f: metrics = json.load(f)
            clustering_metrics_children.append(html.H4(f"Métricas de Clusterização ({metrics.get('algorithm','N/A')}):"))
            ul_items = [html.Li(f"{k.replace('_',' ').capitalize()}: {str(v)}" if isinstance(v, str) else (f"{k.replace('_',' ').capitalize()}: {v:.4f}" if isinstance(v,float) else f"{k.replace('_',' ').capitalize()}: {str(v)}")) for k, v in metrics.items() if k != 'algorithm']
            clustering_metrics_children.append(html.Ul(ul_items))
        else: clustering_metrics_children.append(html.P("Métricas de clusterização (clustering_metrics.json) não encontradas."))
    except Exception as e:
        print(f"Erro ao carregar métricas de clusterização: {e}"); clustering_metrics_children.append(html.P(f"Erro ao carregar métricas de clusterização: {str(e)}"))
        
    try:
        if os.path.exists(pca_img_path):
            encoded_image = base64.b64encode(open(pca_img_path, 'rb').read())
            pca_img_src = f'data:image/png;base64,{encoded_image.decode()}'
    except Exception as e: print(f"Erro ao carregar imagem PCA da clusterização: {e}")
        
    if not ml_metrics_children and not feature_img_src and not clustering_metrics_children and not pca_img_src:
        default_msg_list = [html.P("Resultados de Análise (ML/Cluster) não disponíveis ou não encontrados.")]
        return default_msg_list, "", default_msg_list, "" 

    return ml_metrics_children, feature_img_src, clustering_metrics_children, pca_img_src

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=5000, debug=True)