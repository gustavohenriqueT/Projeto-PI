from flask import Flask, render_template
import pandas as pd
from sqlalchemy import create_engine, text  # Adicione text aqui
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# Configurações do banco com timeout
DB_URI = "postgresql://admin:senha_segura@banco/transporte?connect_timeout=10"

def plot_to_img():
    """Converte gráfico matplotlib para imagem base64"""
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    plt.close()
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

@app.route('/')
def dashboard():
    try:
        engine = create_engine(DB_URI)
        df = pd.read_sql('SELECT * FROM dados_transporte', engine)
        
        # Verificação reforçada
        if 'data_hora' not in df.columns:
            return "Erro: Coluna 'data_hora' não encontrada no banco", 500
            
        df['data_hora'] = pd.to_datetime(df['data_hora'], errors='coerce')
        if df['data_hora'].isna().all():
            return "Erro: Datas inválidas na coluna 'data_hora'", 500

        # Gráfico 1: Passageiros por horário
        plt.figure(figsize=(10, 5))
        df.groupby(df['data_hora'].dt.hour)['passageiros'].mean().plot(
            kind='bar',
            color='skyblue'
        )
        plt.title('Média de Passageiros por Hora', pad=20)
        plt.xlabel('Hora do Dia')
        plt.ylabel('Passageiros')
        plt.xticks(rotation=0)
        img1 = plot_to_img()
        
        # Gráfico 2: Situação das viagens
        plt.figure(figsize=(6, 6))
        df['situacao'].value_counts().plot.pie(
            autopct='%1.1f%%',
            startangle=90,
            colors=['lightgreen', 'lightcoral']
        )
        plt.title('Distribuição das Viagens', pad=20)
        img2 = plot_to_img()
        
        return render_template('dashboard.html', img1=img1, img2=img2)
    
    except Exception as e:
        app.logger.error(f"Erro no dashboard: {str(e)}")
        return f"Erro no servidor: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)