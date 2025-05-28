FROM bitnami/spark:3.4

USER root

# Instala gcc, python3-dev, build-essential e outras dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    build-essential \
    python3-dev \
    curl \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /opt/bitnami/spark/jars && \
    curl -L https://jdbc.postgresql.org/download/postgresql-42.6.0.jar -o /opt/bitnami/spark/jars/postgresql-jdbc.jar && \
    chmod 644 /opt/bitnami/spark/jars/postgresql-jdbc.jar

COPY . .

USER 1001
