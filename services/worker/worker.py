import os
import time
import requests
import random

# Carregando variáveis do ambiente
HOME_URL = f'{os.getenv("BASE_SCHEDULER_URL")}{os.getenv("SCHEDULER_HOME")}'
GET_CAMPAIGN_URL = f'{os.getenv("BASE_SCHEDULER_URL")}{os.getenv("SCHEDULER_GET_CAMPAIGN")}'
POST_RESULT_URL = f'{os.getenv("BASE_SCHEDULER_URL")}{os.getenv("SCHEDULER_POST_CAMPAIGN_RESULT")}'
CIRCUIT_BREAKER_URL = f'{os.getenv("BASE_SCHEDULER_URL")}{os.getenv("GET_FLAG")}?flag={os.getenv("FLAG_CIRCUIT_BREAKER")}'
JITTER_URL = f'{os.getenv("BASE_SCHEDULER_URL")}{os.getenv("GET_FLAG")}?flag={os.getenv("FLAG_JITTER")}'
PAUSE_TIME_URL = f'{os.getenv("BASE_SCHEDULER_URL")}{os.getenv("SCHEDULER_GET_PAUSE_TIME")}'
YOUTUBE_URL = os.getenv('BASE_YOUTUBE_URL') + os.getenv('YOUTUBE_LIKE_VIDEO')
INSTAGRAM_URL = os.getenv('BASE_INSTAGRAM_URL') + os.getenv('INSTAGRAM_LIKE_VIDEO')
MONITORING_URL = os.getenv('MONITORING_URL')
EVENT_URL = os.getenv('MONITORING_EVENT_URL')

class EnumLogStatus:
    SUCCESS = 'success'
    BLOCK = 'block'

def log_action(plataforma, content_id, status=None):
    if status == EnumLogStatus.SUCCESS:
        requests.post(
            MONITORING_URL,
            params={
                'platform': plataforma,
                'status': 'success',
                'content_id': content_id
            }
        )

    elif status == EnumLogStatus.BLOCK:
        requests.post(
            EVENT_URL,
            params={
                'platform': plataforma,
                'type': 'BLOCK'
            }
        )

        requests.post(
            MONITORING_URL,
            params={
                'platform': plataforma,
                'status': 'blocked',
                'content_id': content_id
            }
        )

    else:
        requests.post(
            MONITORING_URL,
            params={
                'platform': plataforma,
                'status': 'error',
                'content_id': content_id
            }
        )


print('Aguardando scheduler iniciar...')
while True:
    try:
        res = requests.get(HOME_URL)
        if res.status_code == 200:
            print('SCheduler iniciado com sucesso.\n')
            break
    except:
        pass

    time.sleep(1)

print('Worker iniciado. Escutando a fila no scheduler...')


while True:
    tarefa = requests.get(GET_CAMPAIGN_URL).json()
    if not tarefa:
        time.sleep(5)
        continue

    dados = tarefa
    # formato: plataforma:acoes:rate_limit:content_id
    plataforma, acoes, rate_limit, content_id = dados.split(':', 3)
    acoes = int(acoes)
    rate_limit = int(float(rate_limit))
    original_rate_limit = rate_limit
    action_delay = 60 / rate_limit
    deviation = action_delay / 2
    rate_limit_changed = False

    if plataforma == 'youtube':
        url_base = YOUTUBE_URL
    elif plataforma == 'instagram':
        url_base = INSTAGRAM_URL

    url_alvo = f'{url_base}?video_id={content_id}'
    print(
        f'\n[WORKER] Iniciando {acoes} ações no {plataforma} para {content_id}...')

    pause_time = 1
    circuit_open = False

    i = 0
    while i < acoes:
        if circuit_open and requests.get(CIRCUIT_BREAKER_URL).text == '1':
            print(
                f'[{plataforma}/{content_id}] CIRCUIT BREAKER ABERTO! Pausando por {pause_time}s...')
            time.sleep(pause_time)
            circuit_open = False
            print(f'[{plataforma}/{content_id}] Tentando reconectar...')

        try:
            if requests.get(CIRCUIT_BREAKER_URL).text == '1':
                wait_time = min(
                    random.normalvariate(action_delay, deviation),
                    action_delay + deviation
                )
                time.sleep(max(0.1, wait_time))
            else:
                time.sleep(action_delay)

            response = requests.post(url_alvo)

            if response.status_code == 200:
                print(f'[{plataforma}/{content_id}] Ação {i+1} OK')
                log_action(plataforma, content_id, EnumLogStatus.SUCCESS)
                pause_time = 1
            elif response.status_code == 429:
                log_action(plataforma, content_id, EnumLogStatus.BLOCK)
                if not rate_limit_changed:
                    rate_limit_changed = True
                    rate_limit /= 2

                if requests.get(CIRCUIT_BREAKER_URL).text == '1':
                    print(
                        f'[{plataforma}/{content_id}] BLOQUEADO (429)! Abrindo circuito.')
                    circuit_open = True
                    max_pause = int(requests.get(PAUSE_TIME_URL).text or 64)
                    pause_time = min(pause_time * 2, max_pause)
                else:
                    print(
                        f'[{plataforma}/{content_id}] BLOQUEADO (429)! Flag de circuit breaker desligada.')
                i -= 1
            else:
                log_action(plataforma, content_id)
                print(
                    f'[{plataforma}/{content_id}] Resposta inesperada: {response.status_code} - {response.text}')
        except Exception as e:
            print(f'Erro de conexão: {e}')
            break

        i += 1
        time.sleep(0.1)

    try:
        params = {
            'platform': plataforma,
            'rate_limit': original_rate_limit,
            'approved': 0 if rate_limit_changed else 1
        }
        requests.post(POST_RESULT_URL, params=params)
    except Exception as e:
        print(f'Erro de conexão: {e}')
        break
