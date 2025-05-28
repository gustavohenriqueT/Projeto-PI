FROM python:3.9-slim

WORKDIR /app

# 1. Instala dependências do sistema (incluindo dos2unix)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# 2. Configura o wait-for-it
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh && \
    dos2unix /wait-for-it.sh

# 3. Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copia o código da aplicação
COPY . .

# 5. Converte line endings dos arquivos Python
RUN find . -name "*.py" -exec dos2unix {} \;

# 6. Comando de inicialização
CMD ["/wait-for-it.sh", "postgres:5432", "--timeout=30", "--", "gunicorn", "--bind", "0.0.0.0:5000", "--workers=4", "app:server"]