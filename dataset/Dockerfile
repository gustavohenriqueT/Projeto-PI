# dataset/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Instala dependências separadamente para melhor cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /app/dados

COPY generate_dataset.py .

CMD ["python", "generate_dataset.py"]