FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc
RUN pip install --no-cache-dir fastapi uvicorn redis httpx psycopg2-binary
COPY . .