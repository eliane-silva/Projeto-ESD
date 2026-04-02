from fastapi import FastAPI, HTTPException
import os
import requests
import random
import time

# URLs da API
SCHEDULER_CAMPAIGN = os.getenv('SCHEDULER_CAMPAIGN')
ALT_FLAG = os.getenv('ALT_FLAG')
GET_FLAG = os.getenv('GET_FLAG')
SCHEDULER_SET_PAUSE_TIME = os.getenv('SCHEDULER_SET_PAUSE_TIME')
SCHEDULER_GET_PAUSE_TIME = os.getenv('SCHEDULER_GET_PAUSE_TIME')
SCHEDULER_POST_CAMPAIGN_RESULT = os.getenv('SCHEDULER_POST_CAMPAIGN_RESULT')
SCHEDULER_GET_CAMPAIGN = os.getenv('SCHEDULER_GET_CAMPAIGN')

# Carregando variáveis do ambiente
REDIS_URL = os.getenv('REDIS_URL')
YOUTUBE_LIST_VIDEOS = f'{os.getenv("BASE_YOUTUBE_URL")}{os.getenv("YOUTUBE_LIST_VIDEOS")}'
INSTAGRAM_LIST_VIDEOS = f'{os.getenv("BASE_INSTAGRAM_URL")}{os.getenv("INSTAGRAM_LIST_VIDEOS")}'
FLAG_THRESHOLD = os.getenv('FLAG_THRESHOLD')
FLAG_DYNAMIC_DISTRIBUTION = os.getenv('FLAG_DYNAMIC_DISTRIBUTION')
FLAG_JITTER = os.getenv('FLAG_JITTER')
FLAG_CIRCUIT_BREAKER = os.getenv('FLAG_CIRCUIT_BREAKER')
EVENT_URL = os.getenv('MONITORING_EVENT_URL')

# Parâmetros do Scheduler
VALID_CONTENT = {
    'youtube': {video['video_id'] for video in requests.get(YOUTUBE_LIST_VIDEOS).json().get('videos')},
    'instagram': {video['video_id'] for video in requests.get(INSTAGRAM_LIST_VIDEOS).json().get('videos')},
}
MAX_ALLOWED_RATE_LIMIT = 120
MAX_LOCK_TIME = 120

campaigns_queue = []
campaign_buffer = {
    'youtube': [],
    'instagram': []
}
campaign_lock = {
    'youtube': {'lock': 0, 'time': 0},
    'instagram': {'lock': 0, 'time': 0}
}
max_pause_time = 64
flags = {
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

app = FastAPI(title='Campaign Scheduler')


class EnumLogStatus:
    RATE_INCREASE = 'RATE_INCREASE'
    RATE_DECREASE = 'RATE_DECREASE'

def log_action(platform, status):
    requests.post(
        EVENT_URL,
        params={
            'platform': platform,
            'type': status
        },
        timeout=2
    )

def is_locked(platform):
    if campaign_lock[platform]['lock'] == 0:
        return False

    elapsed = time.time() - campaign_lock[platform]['time']
    if elapsed > MAX_LOCK_TIME:
        campaign_lock[platform]['lock'] = 0
        campaign_lock[platform]['time'] = 0
        return False

    return True


def unlock(platform):
    campaign_lock[platform]['lock'] = 0
    campaign_lock[platform]['time'] = 0


def lock(platform):
    if not is_locked(platform):
        campaign_lock[platform]['lock'] = 1
        campaign_lock[platform]['time'] = time.time()


@app.post(SCHEDULER_CAMPAIGN)
def post_campaign(platform: str, actions: int, content_id: str):
    if platform not in VALID_CONTENT:
        raise HTTPException(status_code=400, detail='Plataforma inválida')

    if content_id not in VALID_CONTENT[platform]:
        raise HTTPException(
            status_code=400, detail='Conteúdo inválido para a plataforma')

    tested_rate_limit = rate_limits[platform]
    rate_limit = min(MAX_ALLOWED_RATE_LIMIT, tested_rate_limit)
    campanha_str = f'{platform}:{actions}:{rate_limit}:{content_id}'

    if not is_locked(platform):
        lock(platform)
        campaigns_queue.append(campanha_str)
        return {
            'message': f'Campanha para {platform} adicionada à fila com {actions} ações.',
            'content_id': content_id,
            'rate_limit': rate_limit
        }
    else:
        campaign_buffer[platform].append(campanha_str)
        return {
            'message': f'Campanha para {platform} guardada no buffer.',
            'content_id': content_id,
            'rate_limit': rate_limit
        }


@app.post(ALT_FLAG)
def alt_flag(flag: str):
    flags[flag] = 1 - flags[flag]


@app.get(GET_FLAG)
def get_flag(flag: str):
    return flags[flag]


@app.post(SCHEDULER_SET_PAUSE_TIME)
def set_pause_time(time: int):
    global max_pause_time
    max_pause_time = time


@app.get(SCHEDULER_GET_PAUSE_TIME)
def get_pause_time():
    return max_pause_time


def increase_rate_limit(platform: str, approved_rate_limit: int):
    if approved_rate_limit < max_rate_limits[platform]:
        safer_rate_limits[platform] = approved_rate_limit
        new_rate_limit = int(
            approved_rate_limit + (max_rate_limits[platform] - approved_rate_limit) / 2)
        new_rate_limit = max(new_rate_limit, approved_rate_limit + 1)
        rate_limits[platform] = new_rate_limit


    log_action(platform, EnumLogStatus.RATE_INCREASE)
    print(f'[{platform}] Velocidade atual aumentada para {rate_limits[platform]}.')


def decrease_rate_limit(platform: str, rejected_rate_limit: int):
    max_rate_limits[platform] = rejected_rate_limit
    if safer_rate_limits[platform] >= rejected_rate_limit:
        safer_rate_limits[platform] = rejected_rate_limit / 2
    new_rate_limit = int(
        rejected_rate_limit - (rejected_rate_limit - safer_rate_limits[platform]) / 2)
    new_rate_limit = min(new_rate_limit, rejected_rate_limit - 1)
    rate_limits[platform] = new_rate_limit

    log_action(platform, EnumLogStatus.RATE_DECREASE)
    print(f'[{platform}] Velocidade atual reduzida para {rate_limits[platform]}.')


@app.post(SCHEDULER_POST_CAMPAIGN_RESULT)
def post_campaign_result(
    platform: str,
    rate_limit: int,
    approved: int
):
    if flags[FLAG_THRESHOLD] == 1:
        if approved == 1:
            increase_rate_limit(platform, rate_limit)
        elif approved == 0:
            decrease_rate_limit(platform, rate_limit)
    else:
        print(f'[{platform}] Flag de threshold desligada.')

    unlock(platform)


@app.get(SCHEDULER_GET_CAMPAIGN)
def get_campaign():
    if len(campaigns_queue) == 0:
        possible_platforms = {}

        for plat in rate_limits.keys():
            if len(campaign_buffer[plat]) > 0 and not is_locked(plat):
                possible_platforms[plat] = rate_limits[plat]

        if possible_platforms:
            plats = list(possible_platforms.keys())

            if flags[FLAG_DYNAMIC_DISTRIBUTION] == 0:
                platform = random.choice(plats)
                print(f'Flag de dynamic distribution desligada.')
                print(f'Uma campanha para [{platform}] foi escolhida de forma aleatória.')
            else:
                weights = list(possible_platforms.values())
                platform = random.choices(plats, weights=weights, k=1)[0]
                print(f'Uma campanha para [{platform}] foi escolhida com base nos pesos {possible_platforms}')

            campaign = campaign_buffer[platform].pop(0)
            lock(platform)
            return campaign
        else:
            print('Não existem campanhas em nenhum buffer.')

    if len(campaigns_queue) > 0:
        campaign = campaigns_queue.pop(0)
        platform, _, _, _ = campaign.split(':')
        lock(platform)
        return campaign
    return None
