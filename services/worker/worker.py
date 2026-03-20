import os
import time
import httpx
import redis

r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
YOUTUBE_URL = os.getenv("YOUTUBE_URL")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL")

print("Worker iniciado. Escutando a fila no Redis...")

while True:
    # brpop trava o worker até chegar algo na fila, consumindo 0% de CPU enquanto espera
    tarefa = r.brpop("fila_campanhas", timeout=5)
    
    if tarefa:
        _, dados = tarefa
        plataforma, acoes = dados.split(":")
        acoes = int(acoes)
        
        url_alvo = YOUTUBE_URL if plataforma.lower() == "youtube" else INSTAGRAM_URL
        print(f"\n[WORKER] Iniciando {acoes} ações no {plataforma}...")
        
        pause_time = 1
        circuit_open = False

        with httpx.Client() as client:
            for i in range(acoes):
                if circuit_open:
                    print(f"[{plataforma}] CIRCUIT BREAKER ABERTO! Pausando por {pause_time}s...")
                    time.sleep(pause_time)
                    circuit_open = False
                    print(f"[{plataforma}] Tentando reconectar...")

                try:
                    time.sleep(0.5) # Throttling / Jitter
                    response = client.post(url_alvo)
                    
                    if response.status_code == 200:
                        print(f"[{plataforma}] Ação {i+1} OK")
                        pause_time = 1
                    elif response.status_code == 429:
                        print(f"[{plataforma}] BLOQUEADO (429)! Abrindo circuito.")
                        circuit_open = True
                        pause_time *= 2 # Exponential Backoff
                except Exception as e:
                    print(f"Erro de conexão: {e}")
                    break