import os
import time
import httpx
import redis
import random
import redis.exceptions
from urllib.parse import urlencode

r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
YOUTUBE_URL = os.getenv('YOUTUBE_URL')
INSTAGRAM_URL = os.getenv('INSTAGRAM_URL')

print('Worker iniciado. Escutando a fila no Redis...')

while True:
    try:
        tarefa = r.brpop('fila_campanhas', timeout=5)
    except redis.exceptions.ConnectionError:
        print("\n[WORKER] Conexão com o Redis perdida! Tentando reconectar em 5s...")
        time.sleep(5)
        continue
    except Exception as e:
        print(f"\n[WORKER] Erro inesperado ao acessar o Redis: {e}")
        time.sleep(5)
        continue

    if not tarefa:
        continue

    _, dados = tarefa
    # formato: plataforma:acoes:rate_limit:content_id
    plataforma, acoes, rate_limit, content_id = dados.split(':', 3)
    acoes = int(acoes)
    rate_limit = int(float(rate_limit))
    original_rate_limit = rate_limit
    action_delay = 60 / rate_limit
    deviation = action_delay / 2
    rate_limit_changed = False

    base_url = YOUTUBE_URL if plataforma.lower() == 'youtube' else INSTAGRAM_URL
    url_alvo = f'{base_url}?{urlencode({"video_id": content_id})}'

    print(f'\n[WORKER] Iniciando {acoes} ações no {plataforma} para {content_id}...')

    pause_time = 1
    circuit_open = False

    with httpx.Client() as client:
        i = 0
        while i < acoes:
            if circuit_open and r.get('flag:circuit_breaker') == '1':
                print(f'[{plataforma}/{content_id}] CIRCUIT BREAKER ABERTO! Pausando por {pause_time}s...')
                time.sleep(pause_time)
                circuit_open = False
                print(f'[{plataforma}/{content_id}] Tentando reconectar...')

            try:
                if r.get('flag:jitter') == '1':
                    wait_time = min(
                        random.normalvariate(action_delay, deviation),
                        action_delay + deviation
                    )
                    time.sleep(max(0.1, wait_time))
                else:
                    time.sleep(action_delay)

                response = client.post(url_alvo)

                if response.status_code == 200:
                    print(f'[{plataforma}/{content_id}] Ação {i+1} OK')
                    pause_time = 1
                elif response.status_code == 429:
                    if not rate_limit_changed:
                        rate_limit_changed = True
                        rate_limit /= 2

                    if r.get('flag:circuit_breaker') == '1':
                        print(f'[{plataforma}/{content_id}] BLOQUEADO (429)! Abrindo circuito.')
                        circuit_open = True
                        max_pause = int(r.get('config:max_pause_time') or 64)
                        pause_time = min(pause_time * 2, max_pause)
                    else:
                        print(f'[{plataforma}/{content_id}] BLOQUEADO (429)! Flag de circuit breaker desligada.')
                    i -= 1
                else:
                    print(f'[{plataforma}/{content_id}] Resposta inesperada: {response.status_code} - {response.text}')
            except Exception as e:
                print(f'Erro de conexão: {e}')
                break

            i += 1
            time.sleep(0.1)

        try:
            if not rate_limit_changed:
                params = {
                    'platform': plataforma,
                    'approved_rate_limit': original_rate_limit
                }
                client.post('http://scheduler:8000/pass', params=params)
            else:
                params = {
                    'platform': plataforma,
                    'rejected_rate_limit': original_rate_limit
                }
                client.post('http://scheduler:8000/throttle', params=params)

            client.post(
                'http://scheduler:8000/unlock',
                params={'platform': plataforma}
            )
        except Exception as e:
            print(f'Erro de conexão: {e}')
            break