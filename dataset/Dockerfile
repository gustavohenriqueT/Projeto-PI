# dataset/Dockerfile
FROM python:3.9-slim as builder

WORKDIR /app
COPY generate_dataset.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /app/dados && \
    python generate_dataset.py

FROM nginx:alpine
COPY --from=builder /app/dados /usr/share/nginx/html