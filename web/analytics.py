import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine
import time
from datetime import datetime

def wait_for_db(max_retries=5, wait_seconds=5):
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                user="admin",
                password=os.getenv("DB_PASSWORD"),
                database="transporte"
            )
            conn.close()
            print("Banco de dados pronto!")
            return True
        except psycopg2.OperationalError as e:
            print(f"⚠️ Tentativa {i+1}/{max_retries} - Banco não está pronto...")
            time.sleep(wait_seconds)
    raise Exception("Não foi possível conectar ao banco após várias tentativas")

def main():
    # 1. Carregar dataset
    print(f"{datetime.now()} - Carregando dataset...")
    df = pd.read_csv(os.getenv("DATASET_URL"))
    
    # 2. Processar dados
    print(f"{datetime.now()} - Processando dados...")
    df = df[df['Dado_Correto'] == True]
    df = df.drop(columns=['Dado_Correto'])
    
    # 3. Esperar banco ficar pronto
    wait_for_db()
    
    # 4. Salvar no PostgreSQL
    print(f"{datetime.now()} - Conectando ao banco...")
    engine