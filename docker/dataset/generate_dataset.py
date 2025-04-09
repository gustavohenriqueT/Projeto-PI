import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Configuração
numRegistros = 5000
linhasTransporte = ["Linha 101", "Linha 202", "Linha 303", "Linha 404", "Linha 505"]
veiculos = [f"Onibus {i}" for i in range(1, 31)]

# Funções para gerar dados
def gerarDataHora(correta=True):
    inicio = datetime(2024, 3, 1, 5, 0, 0)
    if correta:
        delta = timedelta(minutes=random.randint(0, 30 * 24 * 60))
    else:
        if random.random() < 0.1:
            delta = timedelta(days=random.randint(-365, 365))
        else:
            delta = timedelta(minutes=random.randint(-120, 60 * 24 * 60))
    return inicio + delta

def gerarLocalizacao(correta=True):
    if correta:
        lat = round(random.uniform(-23.55, -23.60), 6)
        lon = round(random.uniform(-46.63, -46.68), 6)
    else:
        if random.random() < 0.05:
            lat = round(random.uniform(-90, 90), 6)
            lon = round(random.uniform(-180, 180), 6)
        else:
            lat = round(random.uniform(-23.50, -23.65), 6)
            lon = round(random.uniform(-46.60, -46.70), 6)
    return lat, lon

def gerarPassageiros(correta=True):
    if correta:
        return random.randint(0, 40)
    else:
        if random.random() < 0.05:
            return random.randint(100, 200)
        else:
            return random.randint(-10, 50)

def gerarTempoViagem(correta=True):
    if correta:
        return random.randint(10, 90)
    else:
        if random.random() < 0.05:
            return random.randint(-30, 500)
        else:
            return random.randint(5, 150)

def gerarVeiculo(correta=True):
    if correta:
        return random.choice(veiculos)
    else:
        if random.random() < 0.05:
            return f"Veiculo {random.randint(100, 200)}"
        else:
            return random.choice(veiculos)

def gerarLinha(correta=True):
    if correta:
        return random.choice(linhasTransporte)
    else:
        if random.random() < 0.05:
            return f"Linha {random.randint(600, 700)}"
        else:
            return random.choice(linhasTransporte)

# Gerar dados - cerca de 85% corretos e 15% com problemas
dados = {
    "Data_Hora": [],
    "ID_Veiculo": [],
    "Linha": [],
    "Latitude": [],
    "Longitude": [],
    "Numero_Passageiros": [],
    "Tempo_Viagem_Minutos": [],
    "Dado_Correto": []
}

for _ in range(numRegistros):
    correto = random.random() < 0.85

    dados["Data_Hora"].append(gerarDataHora(correto))
    dados["ID_Veiculo"].append(gerarVeiculo(correto))
    dados["Linha"].append(gerarLinha(correto))
    
    lat, lon = gerarLocalizacao(correto)
    dados["Latitude"].append(lat)
    dados["Longitude"].append(lon)
    
    dados["Numero_Passageiros"].append(gerarPassageiros(correto))
    dados["Tempo_Viagem_Minutos"].append(gerarTempoViagem(correto))
    dados["Dado_Correto"].append(correto)

# Criar DataFrame
df = pd.DataFrame(dados)

df["Data_Hora"] = pd.to_datetime(df["Data_Hora"], errors='coerce')
df["Hora"] = df["Data_Hora"].dt.hour

limiar_pico = df[df["Dado_Correto"]]["Numero_Passageiros"].quantile(0.75)

df["Horario_Pico"] = (df["Numero_Passageiros"] >= limiar_pico).astype(int)

df["Situacao"] = df["Horario_Pico"].apply(lambda x: "Lenta" if x == 1 else "Rapida")

df.to_csv("dataset.csv", index=False)

print("Dataset 'dataset.csv' gerado com sucesso!")
print(f"Proporção de dados corretos: {df['Dado_Correto'].mean():.2%}")
print(df["Situacao"].value_counts())