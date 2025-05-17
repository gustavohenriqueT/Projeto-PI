import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuração
num_records = 5000
transport_lines = ["Linha 101", "Linha 202", "Linha 303"]

def generate_data():
    data = {
        "timestamp": [datetime.now() - timedelta(minutes=i) for i in range(num_records)],
        "line": [np.random.choice(transport_lines) for _ in range(num_records)],
        "passengers": np.random.randint(0, 50, num_records),
        "lat": np.random.uniform(-23.55, -23.60, num_records),
        "lon": np.random.uniform(-46.63, -46.68, num_records)
    }
    df = pd.DataFrame(data)
    df.to_csv("/data/transport_data.csv", index=False)

if __name__ == "__main__":
    generate_data()