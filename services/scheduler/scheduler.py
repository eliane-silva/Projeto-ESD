from fastapi import FastAPI
import redis
import os
import random

app = FastAPI(title="Campaign Scheduler")
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

MAX_ALLOWED_RATE_LIMIT = 120
MAX_LOCK_TIME = 120
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
    lock_key = f"lock:{platform}"
    buffer_key = f"buffer:{platform}"

    tested_rate_limit = rate_limits[platform]
    rate_limit = min(MAX_ALLOWED_RATE_LIMIT, tested_rate_limit)
    campanha_str = f"{platform}:{actions}:{rate_limit}"

    acquired = r.set(lock_key, 1, nx=True, ex=MAX_LOCK_TIME)
    if acquired:
        # Publica a tarefa na fila do Redis
        r.lpush("fila_campanhas", campanha_str)
        return {"message": f"Campanha para {platform} adicionada à fila (Redis) com {actions} ações!"}
    else:
        # Lock ocupado → campanha vai pro buffer
        r.rpush(buffer_key, campanha_str)
        return {"message": f"Campanha para {platform} guardada no buffer."}


@app.post("/pass")
def increase_rate_limit(platform: str, approved_rate_limit: int):
    if r.get("flag:threshold") == "1":
        if approved_rate_limit < max_rate_limits[platform]:
            safer_rate_limits[platform] = approved_rate_limit
            rate_limits[platform] = int(
                approved_rate_limit + (max_rate_limits[platform] - approved_rate_limit) / 2)
        print(
            f"[{platform}] Velocidade atual aumentada para {rate_limits[platform]}.")
    else:
        print(f"[{platform}] Flag de threshold desligada.")


@app.post("/throttle")
def decrease_rate_limit(platform: str, rejected_rate_limit: int):
    if r.get("flag:threshold") == "1":
        max_rate_limits[platform] = rejected_rate_limit
        if safer_rate_limits[platform] >= rejected_rate_limit:
            safer_rate_limits[platform] = rejected_rate_limit / 2
        rate_limits[platform] = int(
            rejected_rate_limit - (rejected_rate_limit - safer_rate_limits[platform]) / 2)
        print(f"[{platform}] Velocidade atual reduzida para {rate_limits[platform]}.")
    else:
        print(f"[{platform}] Flag de threshold desligada.")


@app.post("/unlock")
def unlock_platform(platform: str):
    lock_key = f"lock:{platform}"

    # Remove o lock
    r.delete(lock_key)

    if r.llen("fila_campanhas") == 0:
        if r.get("flag:dynamic_distribution") == "1":
            possible_platforms = dict()

            for plat in rate_limits.keys():
                buffer_key = f"buffer:{plat}"
                lock_key = f"lock:{plat}"

                if r.llen(buffer_key) > 0 and r.get(lock_key) is None:
                    possible_platforms[plat] = rate_limits[plat]

            weights = []
            if possible_platforms:
                plats = list(possible_platforms.keys())
                weights = list(possible_platforms.values())

                # escolha ponderada
                platform = random.choices(plats, weights=weights, k=1)[0]

            if weights:
                print(
                    f"Uma campanha para a plataforma [{platform}] foi escolhida com base nos pesos {possible_platforms}")
        else:
            print(f"[{platform}] Flag de dynamic distribution desligada.")


        # Verifica se tem campanha no buffer
        lock_key = f"lock:{platform}"
        buffer_key = f"buffer:{platform}"
        next_campanha = r.lpop(buffer_key)
        if next_campanha:
            _, actions, _ = next_campanha.split(":")
            tested_rate_limit = rate_limits[platform]
            rate_limit = min(MAX_ALLOWED_RATE_LIMIT, tested_rate_limit)
            campanha_str = f"{platform}:{actions}:{rate_limit}"

            # Adquire o lock de novo
            r.set(lock_key, "1", nx=True, ex=MAX_LOCK_TIME)
            # Coloca na fila para o worker processar
            r.lpush("fila_campanhas", campanha_str)
            print(f"[{platform}] Campanha do buffer movida para a fila")
