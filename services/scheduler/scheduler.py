from fastapi import FastAPI
import redis
import os

app = FastAPI(title="Campaign Scheduler")
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

@app.post("/start_campaign")
def start(platform: str, actions: int):
    # Publica a tarefa na fila do Redis
    r.lpush("fila_campanhas", f"{platform}:{actions}")
    return {"message": f"Campanha para {platform} adicionada à fila (Redis) com {actions} ações!"}