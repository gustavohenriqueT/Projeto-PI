import os
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
# import psycopg2 # Comentado ou removido
# from psycopg2 import sql # Comentado ou removido
# import psycopg2.extras # Comentado ou removido

# Configurações
NUM_REGISTROS = 20000 #
LINHAS_TRANSPORTE = ["Linha 101", "Linha 202", "Linha 303", "Linha 404", "Linha 505"] #
VEICULOS = [f"Ônibus {i}" for i in range(1, 31)] #
DIRETORIO_DADOS = "/app/data/"  # Caminho dentro do container #

# Funções para gerar dados
def gerar_data_hora(): #
    """Gera data e hora aleatória dentro de 30 dias a partir de 1/3/2024 05:00"""
    inicio = datetime(2024, 3, 1, 5, 0, 0) #
    delta = timedelta(minutes=random.randint(0, 30 * 24 * 60)) #
    return inicio + delta #

def gerar_localizacao(): #
    """Gera coordenadas aleatórias na região de São Paulo"""
    lat = round(random.uniform(-23.55, -23.60), 6) #
    lon = round(random.uniform(-46.63, -46.68), 6) #
    return lat, lon #

def gerar_dados_sinteticos(num_registros): #
    """Gera DataFrame com dados sintéticos de transporte"""
    dados = { #
        "data_hora": [gerar_data_hora() for _ in range(num_registros)], #
        "id_veiculo": [random.choice(VEICULOS) for _ in range(num_registros)], #
        "linha": [random.choice(LINHAS_TRANSPORTE) for _ in range(num_registros)], #
        "latitude": [], #
        "longitude": [], #
        "numero_passageiros": [random.randint(0, 40) for _ in range(num_registros)], #
        "tempo_viagem_minutos": [random.randint(10, 90) for _ in range(num_registros)], #
    }
    
    # Gerar coordenadas
    for _ in range(num_registros): #
        lat, lon = gerar_localizacao() #
        dados["latitude"].append(lat) #
        dados["longitude"].append(lon) #
    
    df = pd.DataFrame(dados) #
    
    # Processamento adicional
    df["data_hora"] = pd.to_datetime(df["data_hora"]) #
    df["hora"] = df["data_hora"].dt.hour #
    limiar_pico = df["numero_passageiros"].quantile(0.75) #
    df["horario_pico"] = (df["numero_passageiros"] >= limiar_pico).astype(int) #
    df["situacao"] = ["Rapida" if pico == 1 else "Lenta" for pico in df["horario_pico"]] #
    
    return df #

def salvar_para_csv(df, diretorio): #
    """Salva os dados em arquivo CSV"""
    os.makedirs(diretorio, exist_ok=True) #
    caminho_arquivo = os.path.join(diretorio, "transport_data.csv") #
    if os.path.exists(caminho_arquivo):  #
        os.remove(caminho_arquivo) #
    df.to_csv(caminho_arquivo, index=False) #
    print(f"Dados salvos em: {caminho_arquivo}") #
    return caminho_arquivo #

# def importar_para_postgres(df): # Removido ou comentado
#     """Importa os dados para um banco PostgreSQL"""
#     try:
#         conn = psycopg2.connect(
#             host="postgres",
#             database="transport_db",
#             user="admin",
#             password="password",
#             port="5432"
#         )
#         cur = conn.cursor()
        
#         # Cria a tabela se não existir
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS transport_data (
#                 id SERIAL PRIMARY KEY,
#                 data_hora TIMESTAMP,
#                 id_veiculo VARCHAR(50),
#                 linha VARCHAR(50),
#                 latitude FLOAT,
#                 longitude FLOAT,
#                 numero_passageiros INTEGER,
#                 tempo_viagem_minutos INTEGER,
#                 hora INTEGER,
#                 horario_pico BOOLEAN,
#                 situacao VARCHAR(50)
#             );
#         """)
        
#         # Prepara os dados para inserção
#         cols = ['data_hora', 'id_veiculo', 'linha', 'latitude', 'longitude', 
#                 'numero_passageiros', 'tempo_viagem_minutos', 'hora', 'horario_pico', 'situacao']
#         tuples = [tuple(x) for x in df[cols].to_numpy()]
        
#         # SQL para inserção em massa
#         query = sql.SQL("""
#             INSERT INTO transport_data 
#             (data_hora, id_veiculo, linha, latitude, longitude, 
#              numero_passageiros, tempo_viagem_minutos, hora, horario_pico, situacao) 
#             VALUES %s
#         """)
        
#         # Executa a inserção
#         psycopg2.extras.execute_values( # USO DE psycopg2.extras
#             cur, query, tuples,
#             template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
#             page_size=1000
#         )
        
#         conn.commit()
#         print(f"Dados importados para PostgreSQL (Total: {len(df)} registros)")
        
#     except Exception as e:
#         print(f"Erro ao importar dados: {e}")
#         raise
#     finally:
#         if conn:
#             conn.close()

if __name__ == "__main__":
    # Gera os dados sintéticos
    df = gerar_dados_sinteticos(NUM_REGISTROS) #
    
    # Salva em CSV
    caminho_arquivo = salvar_para_csv(df, DIRETORIO_DADOS) #

    
    # Mostra amostra dos dados gerados
    print("\nAmostra dos dados gerados:") #
    print(df.head()) #