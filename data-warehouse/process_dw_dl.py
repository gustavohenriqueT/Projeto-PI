import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine
from time import sleep, time

# Configurações (ajuste conforme seu ambiente)
DATALAKE_PATH = "/app/data/datalake"
DW_CONFIG = {
    "host": "postgres",
    "database": "transport_db",
    "user": "admin",
    "password": "password",
    "port": "5432"
}
CSV_TIMEOUT = 30  # segundos para esperar pelo CSV

def wait_for_csv(csv_path):
    """Aguarda o arquivo CSV ficar disponível com timeout."""
    start_time = time()
    while not os.path.exists(csv_path):
        if time() - start_time > CSV_TIMEOUT:
            raise FileNotFoundError(f"CSV não encontrado após {CSV_TIMEOUT} segundos em: {csv_path}")
        print(f"Aguardando CSV... ({int(time() - start_time)}s)")
        sleep(1)

def connect_postgres():
    """Tenta conectar ao PostgreSQL com retries."""
    for attempt in range(5):
        try:
            conn = psycopg2.connect(**DW_CONFIG)
            print("✅ Conexão com PostgreSQL estabelecida")
            return conn
        except Exception as e:
            print(f"⚠️ Tentativa {attempt + 1}/5 - Aguardando PostgreSQL... Erro: {str(e).splitlines()[0]}")
            sleep(5)
    raise ConnectionError("❌ Falha ao conectar ao PostgreSQL após 5 tentativas")

def extract_transform(csv_path):
    """Extrai e transforma os dados com verificação robusta."""
    try:
        wait_for_csv(csv_path)
        df = pd.read_csv(csv_path)
        
        required_columns = ['data_hora', 'linha', 'id_veiculo', 'latitude', 'longitude', 
                          'numero_passageiros', 'tempo_viagem_minutos', 'hora', 'horario_pico']
        
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"❌ Colunas faltando no CSV: {missing}\nColunas disponíveis: {list(df.columns)}")
        
        print("✅ CSV validado e processado com sucesso")
        return (
            df[['linha', 'latitude', 'longitude']].drop_duplicates(),
            df[['id_veiculo', 'numero_passageiros', 'tempo_viagem_minutos']].drop_duplicates(),
            df[required_columns]
        )
    except Exception as e:
        print(f"❌ Falha na extração/transformação: {str(e)}")
        raise

def load_to_datalake(dim_linha, dim_onibus, fato_transito):
    """Salva dados no Data Lake com tratamento de erros."""
    try:
        os.makedirs(DATALAKE_PATH, exist_ok=True)
        dim_linha.to_csv(f"{DATALAKE_PATH}/dim_linha.csv", index=False)
        dim_onibus.to_csv(f"{DATALAKE_PATH}/dim_onibus.csv", index=False)
        fato_transito.to_csv(f"{DATALAKE_PATH}/fato_transito.csv", index=False)
        print(f"✅ Data Lake atualizado em: {DATALAKE_PATH}")
    except Exception as e:
        print(f"❌ Falha ao salvar no Data Lake: {str(e)}")
        raise

def load_to_dw(dim_linha, dim_onibus, fato_transito):
    """Carrega dados no PostgreSQL com transação segura."""
    conn = None
    try:
        conn = connect_postgres()
        engine = create_engine(
            f"postgresql+psycopg2://{DW_CONFIG['user']}:{DW_CONFIG['password']}@"
            f"{DW_CONFIG['host']}:{DW_CONFIG['port']}/{DW_CONFIG['database']}"
        )
        
        with conn.cursor() as cursor:
            cursor.execute("BEGIN")
            
            for name, df in [('dim_linha', dim_linha), 
                            ('dim_onibus', dim_onibus), 
                            ('fato_transito', fato_transito)]:
                df.to_sql(name, engine, if_exists='replace', index=False)
                print(f"✅ Tabela {name} carregada")
            
            cursor.execute("COMMIT")
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Falha no Data Warehouse: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        print("\n=== Iniciando pipeline ===")
        csv_path = "/app/data/transport_data.csv"
        
        dim_linha, dim_onibus, fato_transito = extract_transform(csv_path)
        load_to_datalake(dim_linha, dim_onibus, fato_transito)
        load_to_dw(dim_linha, dim_onibus, fato_transito)
        
        print("=== Pipeline concluído com sucesso ===")
    except Exception as e:
        print(f"\n=== Pipeline falhou: {str(e)} ===")
        exit(1)