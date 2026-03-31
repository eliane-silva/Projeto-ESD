from fastapi import FastAPI, HTTPException
import redis
import os
import requests
import random

# URLs da API
SCHEDULER_CAMPAIGN = os.getenv('SCHEDULER_CAMPAIGN')
ALT_FLAG = os.getenv('ALT_FLAG')
GET_FLAG = os.getenv('GET_FLAG')
SCHEDULER_SET_PAUSE_TIME = os.getenv('SCHEDULER_SET_PAUSE_TIME')
SCHEDULER_GET_PAUSE_TIME = os.getenv('SCHEDULER_GET_PAUSE_TIME')

# Carregando variáveis do ambiente
REDIS_URL = os.getenv('REDIS_URL')
YOUTUBE_LIST_VIDEOS = f'{os.getenv("BASE_YOUTUBE_URL")}{os.getenv("YOUTUBE_LIST_VIDEOS")}'
INSTAGRAM_LIST_VIDEOS = f'{os.getenv("BASE_INSTAGRAM_URL")}{os.getenv("INSTAGRAM_LIST_VIDEOS")}'
FLAG_THRESHOLD = os.getenv('FLAG_THRESHOLD')
FLAG_DYNAMIC_DISTRIBUTION = os.getenv('FLAG_DYNAMIC_DISTRIBUTION')
FLAG_JITTER = os.getenv('FLAG_JITTER')
FLAG_CIRCUIT_BREAKER = os.getenv('FLAG_CIRCUIT_BREAKER')


r = redis.from_url(REDIS_URL, decode_responses=True)

# Parâmetros do Scheduler
MAX_ALLOWED_RATE_LIMIT = 120
MAX_LOCK_TIME = 120
MAX_PAUSE_TIME = 64
FLAGS = {
    FLAG_THRESHOLD: 1,
    FLAG_DYNAMIC_DISTRIBUTION: 1,
    FLAG_JITTER: 1,
    FLAG_CIRCUIT_BREAKER: 1,
}

# Rate Limit estimados
max_rate_limits = {
    'youtube': MAX_ALLOWED_RATE_LIMIT,
    'instagram': MAX_ALLOWED_RATE_LIMIT,
}
safer_rate_limits = {
    'youtube': 0,
    'instagram': 0,
}
rate_limits = {
    'youtube': MAX_ALLOWED_RATE_LIMIT / 2,
    'instagram': MAX_ALLOWED_RATE_LIMIT / 2,
}

VALID_CONTENT = {
    'youtube': {video['video_id'] for video in requests.get(YOUTUBE_LIST_VIDEOS).json().get('videos')},
    'instagram': {video['video_id'] for video in requests.get(INSTAGRAM_LIST_VIDEOS).json().get('videos')},
}

app = FastAPI(title='Campaign Scheduler')


@app.post(SCHEDULER_CAMPAIGN)
def post_campaign(platform: str, actions: int, content_id: str):
    if platform not in VALID_CONTENT:
        raise HTTPException(status_code=400, detail='Plataforma inválida')

    if content_id not in VALID_CONTENT[platform]:
        raise HTTPException(
            status_code=400, detail='Conteúdo inválido para a plataforma')

    lock_key = f'lock:{platform}'
    buffer_key = f'buffer:{platform}'

    tested_rate_limit = rate_limits[platform]
    rate_limit = min(MAX_ALLOWED_RATE_LIMIT, tested_rate_limit)
    campanha_str = f'{platform}:{actions}:{rate_limit}:{content_id}'

    acquired = r.set(lock_key, 1, nx=True, ex=MAX_LOCK_TIME)
    if acquired:
        r.lpush('fila_campanhas', campanha_str)
        return {
            'message': f'Campanha para {platform} adicionada à fila com {actions} ações.',
            'content_id': content_id,
            'rate_limit': rate_limit
        }
    else:
        r.rpush(buffer_key, campanha_str)
        return {
            'message': f'Campanha para {platform} guardada no buffer.',
            'content_id': content_id,
            'rate_limit': rate_limit
        }


@app.post(ALT_FLAG)
def alt_flag(flag: str):
    FLAGS[flag] = 1 - FLAGS[flag]


@app.get(GET_FLAG)
def get_flag(flag: str):
    return FLAGS[flag]


@app.post(SCHEDULER_SET_PAUSE_TIME)
def set_pause_time(time: int):
    global MAX_PAUSE_TIME
    MAX_PAUSE_TIME = time


@app.get(SCHEDULER_GET_PAUSE_TIME)
def get_pause_time():
    return MAX_PAUSE_TIME


@app.post('/pass')
def increase_rate_limit(platform: str, approved_rate_limit: int):
    if FLAGS[FLAG_THRESHOLD] == 1:
        if approved_rate_limit < max_rate_limits[platform]:
            safer_rate_limits[platform] = approved_rate_limit
            rate_limits[platform] = int(
                approved_rate_limit +
                (max_rate_limits[platform] - approved_rate_limit) / 2
            )
        print(
            f'[{platform}] Velocidade atual aumentada para {rate_limits[platform]}.')
    else:
        print(f'[{platform}] Flag de threshold desligada.')


@app.post('/throttle')
def decrease_rate_limit(platform: str, rejected_rate_limit: int):
    if FLAGS[FLAG_THRESHOLD] == 1:
        max_rate_limits[platform] = rejected_rate_limit
        if safer_rate_limits[platform] >= rejected_rate_limit:
            safer_rate_limits[platform] = rejected_rate_limit / 2
        rate_limits[platform] = int(
            rejected_rate_limit -
            (rejected_rate_limit - safer_rate_limits[platform]) / 2
        )
        print(f'[{platform}] Velocidade atual reduzida para {rate_limits[platform]}.')
    else:
        print(f'[{platform}] Flag de threshold desligada.')


@app.post('/unlock')
def unlock_platform(platform: str):
    lock_key = f'lock:{platform}'
    r.delete(lock_key)

    if r.llen('fila_campanhas') == 0:
        if FLAGS[FLAG_DYNAMIC_DISTRIBUTION] == 1:
            possible_platforms = {}

            for plat in rate_limits.keys():
                buffer_key = f'buffer:{plat}'
                lock_key = f'lock:{plat}'
                if r.llen(buffer_key) > 0 and r.get(lock_key) is None:
                    possible_platforms[plat] = rate_limits[plat]

            weights = []
            if possible_platforms:
                plats = list(possible_platforms.keys())
                weights = list(possible_platforms.values())
                platform = random.choices(plats, weights=weights, k=1)[0]

            if weights:
                print(
                    f'Uma campanha para [{platform}] foi escolhida com base nos pesos {possible_platforms}')
        else:
            print(f'[{platform}] Flag de dynamic distribution desligada.')

        lock_key = f'lock:{platform}'
        buffer_key = f'buffer:{platform}'
        next_campanha = r.lpop(buffer_key)
        if next_campanha:
            _, actions, _, content_id = next_campanha.split(':', 3)
            tested_rate_limit = rate_limits[platform]
            rate_limit = min(MAX_ALLOWED_RATE_LIMIT, tested_rate_limit)
            campanha_str = f'{platform}:{actions}:{rate_limit}:{content_id}'

            r.set(lock_key, '1', nx=True, ex=MAX_LOCK_TIME)
            r.lpush('fila_campanhas', campanha_str)
            print(
                f'[{platform}] Campanha do buffer movida para a fila para {content_id}')
