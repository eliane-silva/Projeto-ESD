from fastapi import FastAPI, HTTPException, Request
import redis
import os
import time

app = FastAPI()

# Conecta ao Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
r = redis.from_url(redis_url, decode_responses=True)

# Configuração do Rate Limit
RATE_LIMIT = 50       # Máximo de requisições
TIME_WINDOW = 60      # Em segundos (1 minuto)

@app.post("/api/v1/youtube/like")
async def like_video(request: Request):
    # Identifica o cliente pelo IP (no Docker, será o IP do container do bot)
    client_ip = request.client.host
    redis_key = f"rate_limit:{client_ip}"

    # Incrementa o contador de requisições no Redis
    requests = r.incr(redis_key)
    
    # Se for a primeira requisição, define o tempo de expiração da chave
    if requests == 1:
        r.expire(redis_key, TIME_WINDOW)

    # Verifica se passou do limite
    if requests > RATE_LIMIT:
        raise HTTPException(
            status_code=429, 
            detail="Too Many Requests. Você foi bloqueado pelo algoritmo do YouTube."
        )

    # Simula um pequeno atraso na resposta do servidor
    time.sleep(0.1)
    
    return {
        "status": "success", 
        "message": "Like computado com sucesso!", 
        "requests_in_window": requests
    }