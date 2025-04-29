from flask import Flask, render_template
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# Configurações do banco
DB_URI = "postgresql://admin:senha_segura@banco/transporte"

@app.route('/')
def dashboard():
    # Conexão com o banco
    engine = create_engine(DB_URI)
    df = pd.read_sql('SELECT * FROM dados_transporte', engine)
    
    # Gráfico 1: Passageiros por horário
    plt.figure(figsize=(10, 5))
    df.groupby(df['data_hora'].dt.hour)['passageiros'].mean().plot(kind='bar')
    plt.title('Média de Passageiros por Hora')
    plt.xlabel('Hora do Dia')
    plt.ylabel('Passageiros')
    img1 = plot_to_img()
    
    # Gráfico 2: Situação das viagens
    plt.figure(figsize=(6, 6))
    df['situacao'].value_counts().plot.pie(autopct='%1.1f%%')
    img2 = plot_to_img()
    
    return render_template('dashboard.html', img1=img1, img2=img2)

def plot_to_img():
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)