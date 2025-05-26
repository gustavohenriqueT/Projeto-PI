import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine
from time import sleep, time

# Configurações
DW_CONFIG = {
    "host": "postgres", #
    "database": "transport_db", #
    "user": "admin", #
    "password": "password", #
    "port": "5432" #
}
CSV_TIMEOUT = 60
R_PROCESSED_CSV_PATH = "/app/data/transport_dataL.csv"

def wait_for_csv(csv_path):
    start_time = time() #
    while not os.path.exists(csv_path): #
        if time() - start_time > CSV_TIMEOUT: #
            raise FileNotFoundError(f"CSV não encontrado após {CSV_TIMEOUT} segundos em: {csv_path}")
        print(f"Aguardando CSV '{os.path.basename(csv_path)}'... ({int(time() - start_time)}s)")
        sleep(1) #
    print(f"✅ CSV '{os.path.basename(csv_path)}' encontrado.")

def connect_postgres():
    for attempt in range(5): #
        try:
            conn = psycopg2.connect(**DW_CONFIG) #
            print("✅ Conexão com PostgreSQL estabelecida.") #
            return conn
        except Exception as e:
            print(f"⚠️ Tentativa {attempt + 1}/5 - Aguardando PostgreSQL... Erro: {str(e).splitlines()[0]}") #
            sleep(5) #
    raise ConnectionError("❌ Falha ao conectar ao PostgreSQL após 5 tentativas.") #

def extract_and_prepare_main_data(csv_path):
    try:
        wait_for_csv(csv_path)
        df = pd.read_csv(csv_path) #
        
        required_r_columns = ['data_hora', 'id_veiculo', 'linha', 'latitude', 'longitude', 
                              'numero_passageiros', 'tempo_viagem_minutos', 'hora', 'horario_pico']
        
        missing = [col for col in required_r_columns if col not in df.columns]
        if missing:
            raise ValueError(f"❌ Colunas faltando no CSV R-processado '{csv_path}': {missing}\nColunas disponíveis: {list(df.columns)}")

        # Modificação para tratar o erro de formato de data:
        print(f"Tentando converter a coluna 'data_hora' para datetime. Primeiros valores: {df['data_hora'].head().to_list()}")
        df['data_hora'] = pd.to_datetime(df['data_hora'], errors='coerce', format='mixed')
        print(f"Conversão de 'data_hora' completa. Verificando por valores nulos (NaT) após conversão...")
        
        rows_with_nat_before = df['data_hora'].isnull().sum()
        if rows_with_nat_before > 0:
            print(f"⚠️ Encontrados {rows_with_nat_before} valores nulos (NaT) na coluna 'data_hora' após pd.to_datetime. Estas linhas serão removidas.")
            df.dropna(subset=['data_hora'], inplace=True)
            print(f"Linhas com 'data_hora' nula removidas. Total de linhas restantes: {len(df)}")
        
        if df.empty:
            raise ValueError("❌ DataFrame vazio após tratamento de datas nulas na coluna 'data_hora'. Verifique o arquivo CSV de entrada e o processo de conversão de datas.")

        df['horario_pico'] = df['horario_pico'].astype(bool)
        df['hora'] = df['hora'].astype(int)

        df_for_dw = df[required_r_columns]
        
        print(f"✅ CSV '{os.path.basename(csv_path)}' validado e dados preparados para tabela 'transport_data'. Linhas: {len(df_for_dw)}")
        return df_for_dw
        
    except Exception as e:
        print(f"❌ Falha na extração/preparação dos dados de '{csv_path}': {str(e)}") #
        raise #

def load_main_data_to_dw(df):
    conn = None # Este 'conn' será uma conexão psycopg2
    try:
        conn = connect_postgres() # Retorna uma conexão psycopg2
        engine_url = f"postgresql+psycopg2://{DW_CONFIG['user']}:{DW_CONFIG['password']}@{DW_CONFIG['host']}:{DW_CONFIG['port']}/{DW_CONFIG['database']}" #
        engine = create_engine(engine_url) # Cria um engine SQLAlchemy
        
        table_name = 'transport_data'
        
        # Operação de TRUNCATE usando a conexão psycopg2 (conn)
        with conn.cursor() as cursor: #
            print(f"Limpando dados existentes da tabela '{table_name}'...")
            cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
            conn.commit() #

        print(f"Carregando novos dados para '{table_name}' ({len(df)} linhas)...")
        if not df.empty:
            # df.to_sql usa o engine SQLAlchemy. Esta parte está correta.
            df.to_sql(table_name, engine, if_exists='append', index=False, method='multi', chunksize=1000) #
            print(f"✅ Tabela '{table_name}' atualizada com {len(df)} registros do CSV processado pelo R.")
        else:
            print(f"⚠️ Tabela '{table_name}' não atualizada pois não havia dados válidos após o processamento.")
            
    except Exception as e:
        # O erro f405 seria capturado aqui.
        # Precisamos ver a mensagem de erro completa que veio ANTES do "(Background on this error...)"
        print(f"❌ Falha ao carregar dados na tabela '{table_name}' do Data Warehouse: {str(e)}") #
        if conn and hasattr(conn, 'rollback'): # Verifica se conn não é None e tem o método rollback
             conn.rollback() #
        raise #
    finally:
        if conn and hasattr(conn, 'close'): # Verifica se conn não é None e tem o método close
            conn.close() #

if __name__ == "__main__":
    try:
        print("\n=== Iniciando pipeline do Data Warehouse (com dados processados pelo R para tabela principal) ===")
        
        df_main_transport_data = extract_and_prepare_main_data(R_PROCESSED_CSV_PATH)
        load_main_data_to_dw(df_main_transport_data)
        
        print("=== Pipeline do Data Warehouse (tabela principal) concluído com sucesso ===")
    except Exception as e:
        print(f"\n=== Pipeline do Data Warehouse (tabela principal) falhou: {str(e)} ===") #
        exit(1) #