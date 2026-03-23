import os
import time
import httpx
import redis
import random

r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
YOUTUBE_URL = os.getenv("YOUTUBE_URL")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL")

print("Worker iniciado. Escutando a fila no Redis...")

while True:
    # brpop trava o worker até chegar algo na fila, consumindo 0% de CPU enquanto espera
    tarefa = r.brpop("fila_campanhas", timeout=5)

    if tarefa:
        _, dados = tarefa
        plataforma, acoes, rate_limit = dados.split(":")
        rate_limit = int(float(rate_limit))
        original_rate_limit = rate_limit
        acoes = int(acoes)
        action_delay = 60 / rate_limit
        deviation = action_delay / 2
        rate_limit_changed = False

        url_alvo = YOUTUBE_URL if plataforma.lower() == "youtube" else INSTAGRAM_URL
        print(f"\n[WORKER] Iniciando {acoes} ações no {plataforma}...")

        pause_time = 1
        circuit_open = False

        with httpx.Client() as client:
            i = 0
            while i < acoes:
                if circuit_open and r.get("flag:circuit_breaker") == "1":
                    print(
                        f"[{plataforma}] CIRCUIT BREAKER ABERTO! Pausando por {pause_time}s...")
                    time.sleep(pause_time)
                    circuit_open = False
                    print(f"[{plataforma}] Tentando reconectar...")

                try:
                    if r.get("flag:jitter") == "1":
                        # Throttling / Jitter
                        wait_time = min(random.normalvariate(
                            action_delay, deviation), action_delay + deviation)
                        time.sleep(
                            max(0.1, wait_time))
                    else:
                        time.sleep(action_delay)

                    response = client.post(url_alvo)

                    if response.status_code == 200:
                        print(f"[{plataforma}] Ação {i+1} OK")
                        pause_time = 1
                    elif response.status_code == 429:
                        if not rate_limit_changed:
                            rate_limit_changed = True
                            rate_limit /= 2

                        if r.get("flag:circuit_breaker") == "1":
                            print(
                                f"[{plataforma}] BLOQUEADO (429)! Abrindo circuito.")
                            circuit_open = True
                            pause_time *= 2  # Exponential Backoff
                        else:
                            print(
                                f"[{plataforma}] BLOQUEADO (429)! Flag de circuit breaker desligada.")
                        i -= 1
                except Exception as e:
                    print(f"Erro de conexão: {e}")
                    break
                i += 1
                time.sleep(0.1)

            try:
                if not rate_limit_changed:
                    params = {
                        "platform": plataforma,
                        "approved_rate_limit": original_rate_limit
                    }
                    response = client.post(
                        "http://scheduler:8000/pass", params=params)
                else:
                    params = {
                        "platform": plataforma,
                        "rejected_rate_limit": original_rate_limit
                    }
                    response = client.post(
                        "http://scheduler:8000/throttle", params=params)
            except Exception as e:
                print(f"Erro de conexão: {e}")
                break
