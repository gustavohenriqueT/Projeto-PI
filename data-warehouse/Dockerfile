FROM python:3.9-slim

WORKDIR /app

# Instala apenas dependências essenciais
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia apenas o script necessário
COPY process_dw_dl.py .

# Comando direto
CMD ["python", "process_dw_dl.py"]