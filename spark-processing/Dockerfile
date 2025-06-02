FROM bitnami/spark:3.4

USER root

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    build-essential \
    python3-dev \
    libpython3-dev \
    cython3 \
    curl \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Criar diretório da aplicação
WORKDIR /app

# Instalar as bibliotecas pesadas primeiro (para cache eficiente)
COPY requirements.txt .  

# Separar nltk
RUN pip install --no-cache-dir --upgrade pip

# Instalar pacotes exceto nltk
RUN grep -v "nltk" requirements.txt > temp_reqs.txt && \
    pip install --no-cache-dir -r temp_reqs.txt

# Instalar nltk separadamente (evita travamentos)
RUN pip install --no-cache-dir nltk==3.8.1

# Instalar recursos NLTK diretamente (evita downloads em tempo de execução)
RUN mkdir -p /app/nltk_data && \
    python3 -m nltk.downloader -d /app/nltk_data stopwords rslp

# Variável de ambiente para nltk_data
ENV NLTK_DATA=/app/nltk_data

# JDBC driver do PostgreSQL
RUN mkdir -p /opt/bitnami/spark/jars && \
    curl -L https://jdbc.postgresql.org/download/postgresql-42.6.0.jar -o /opt/bitnami/spark/jars/postgresql-jdbc.jar && \
    chmod 644 /opt/bitnami/spark/jars/postgresql-jdbc.jar

# Copiar todo o restante do código
COPY . .

USER 1001
