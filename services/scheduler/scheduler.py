from fastapi import FastAPI
import redis
import os

app = FastAPI(title="Campaign Scheduler")
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

MAX_ALLOWED_RATE_LIMIT = 120
max_rate_limits = {
    "youtube": MAX_ALLOWED_RATE_LIMIT,
    "instagram": MAX_ALLOWED_RATE_LIMIT,
}
safer_rate_limits = {
    "youtube": 0,
    "instagram": 0,
}
rate_limits = {
    "youtube": MAX_ALLOWED_RATE_LIMIT / 2,
    "instagram": MAX_ALLOWED_RATE_LIMIT / 2,
}


@app.post("/start_campaign")
def start(platform: str, actions: int):
    tested_rate_limit = rate_limits[platform]
    rate_limit = min(MAX_ALLOWED_RATE_LIMIT, tested_rate_limit)

    # Publica a tarefa na fila do Redis
    r.lpush("fila_campanhas", f"{platform}:{actions}:{rate_limit}")
    return {"message": f"Campanha para {platform} adicionada à fila (Redis) com {actions} ações!"}


@app.post("/pass")
def increase_rate_limit(platform: str, approved_rate_limit: int):
    if r.get("flag:threshold") == "1":
        if approved_rate_limit < max_rate_limits[platform]:
            safer_rate_limits[platform] = approved_rate_limit
            rate_limits[platform] = int(approved_rate_limit + (max_rate_limits[platform] - approved_rate_limit) / 2)
        print(f"[{platform}] Velocidade atual aumentada para {rate_limits[platform]}.")
    else:
        print(f"[{platform}] Flag de threshold desligada.")


@app.post("/throttle")
def decrease_rate_limit(platform:str, rejected_rate_limit: int):
    if r.get("flag:threshold") == "1":
        max_rate_limits[platform] = rejected_rate_limit
        if safer_rate_limits[platform] >= rejected_rate_limit:
            safer_rate_limits[platform] = rejected_rate_limit / 2
        rate_limits[platform] = int(rejected_rate_limit - (rejected_rate_limit - safer_rate_limits[platform]) / 2)
        print(f"[{platform}] Velocidade atual reduzida para {rate_limits[platform]}.")
    else:
        print(f"[{platform}] Flag de threshold desligada.")
