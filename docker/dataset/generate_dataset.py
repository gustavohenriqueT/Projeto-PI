import pandas as pd
import numpy as np

# Configuração
np.random.seed(42)
num_entries = 10_000

# Geração de dados
data = {
    "id": range(1, num_entries + 1),
    "valor": np.random.normal(50, 15, num_entries),
    "categoria": np.random.choice(["A", "B", "C", "D"], num_entries),
    "timestamp": pd.date_range("2023-01-01", periods=num_entries, freq="T")
}

# Salvamento
df = pd.DataFrame(data)
df.to_csv("dados/dataset.csv", index=False)
print(f"Dataset gerado com {len(df)} registros!")