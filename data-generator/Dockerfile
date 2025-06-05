FROM python:3.9-slim

WORKDIR /app

# Instala dependências do sistema para pandas e psycopg2
RUN apt-get update && \
    apt-get install -y gcc g++ python3-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generate_data.py .

RUN mkdir -p /app/data

CMD ["python", "generate_data.py"]
