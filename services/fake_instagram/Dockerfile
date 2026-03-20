FROM python:3.11-slim
WORKDIR /app
# Instalamos os pacotes direto aqui para não precisar do requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn redis httpx
COPY . .