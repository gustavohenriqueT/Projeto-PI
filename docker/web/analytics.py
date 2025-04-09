# analytics.py
import psycopg2
import pandas as pd

# Banco de dados
conn = psycopg2.connect(
    host="192.168.60.20",
    user="admin",
    password="senha_segura",
    database="bigdata"
)

# Dataset
df = pd.read_csv("http://192.168.60.30/dataset.csv")

# Análise (exemplo)
print(df.groupby('categoria')['valor'].mean())