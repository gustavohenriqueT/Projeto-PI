import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine
import time
from datetime import datetime

def wait_for_db():
    """Aguarda o banco ficar disponível"""
    max_retries = 10
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                user="admin",
                password=os.getenv("DB_PASSWORD"),
                database="transporte",
                connect_timeout=3
            )
            conn.close()
            print("✅ Banco pronto!")
            return
        except psycopg2.OperationalError as e:
            print(f"⏳ Tentativa {i+1}/{max_retries} - Banco não está pronto...")
            time.sleep(5)
    raise Exception("❌ Falha ao conectar no banco após várias tentativas")

def main():
    print("\n=== INICIANDO PROCESSAMENTO ===")
    
    # 1. Carregar dataset
    print(f"{datetime.now()} - Carregando dataset...")
    df = pd.read_csv(os.getenv("DATASET_URL"))
    
    # 2. Processar dados
    print(f"{datetime.now()} - Filtrando dados válidos...")
    df = df[df['Dado_Correto'] == True].drop(columns=['Dado_Correto'])
    
    # 3. Esperar banco
    wait_for_db()
    
    # 4. Salvar no PostgreSQL
    print(f"{datetime.now()} - Conectando ao banco...")
    engine = create_engine(
        f"postgresql://admin:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/transporte"
    )
    
    print(f"{datetime.now()} - Salvando dados...")
    df.to_sql('dados_transporte', engine, if_exists='replace', index=False)
    print(f"{datetime.now()} - ✅ Dados salvos com sucesso!")

if __name__ == "__main__":
    main()