from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import redis
import os
import requests
import random
import time

from config import settings

# Conexão com Redis
r = redis.from_url(settings.redis_url, decode_responses=True)

# Parâmetros do Scheduler
VALID_CONTENT = {
    'youtube': set(),
    'instagram': set(),
}

def fetch_valid_content():
    """Busca os IDs de vídeos válidos das APIs de mock."""
    try:
        yt_resp = requests.get(settings.youtube_list_url, timeout=5)
        if yt_resp.status_code == 200:
            VALID_CONTENT['youtube'] = {video['video_id'] for video in yt_resp.json().get('videos', [])}
            print(f"IDs do YouTube carregados: {len(VALID_CONTENT['youtube'])}")
        
        ig_resp = requests.get(settings.instagram_list_url, timeout=5)
        if ig_resp.status_code == 200:
            VALID_CONTENT['instagram'] = {video['video_id'] for video in ig_resp.json().get('videos', [])}
            print(f"IDs do Instagram carregados: {len(VALID_CONTENT['instagram'])}")
    except Exception as e:
        print(f"Erro ao carregar conteúdos válidos: {e}")

MAX_ALLOWED_RATE_LIMIT = 120
MAX_LOCK_TIME = 120

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar conteúdo válido
    fetch_valid_content()

    # Inicializar flags
    for flag in [settings.flag_threshold, settings.flag_dynamic_distribution, settings.flag_jitter, settings.flag_circuit_breaker]:
        if r.get(f'flag:{flag}') is None:
            r.set(f'flag:{flag}', 1)
    if r.get('config:max_pause_time') is None:
        r.set('config:max_pause_time', 64)
    
    yield

app = FastAPI(title='Campaign Scheduler', lifespan=lifespan)


class EnumLogStatus:
    RATE_INCREASE = 'RATE_INCREASE'
    RATE_DECREASE = 'RATE_DECREASE'

def log_action(platform, status):
    requests.post(
        settings.monitoring_event_url,
        params={
            'platform': platform,
            'type': status
        },
        timeout=2
    )

def is_locked(platform):
    lock_key = f'lock:{platform}'
    return r.get(lock_key) is not None


def unlock(platform):
    lock_key = f'lock:{platform}'
    r.delete(lock_key)


def lock(platform):
    lock_key = f'lock:{platform}'
    r.set(lock_key, 1, nx=True, ex=MAX_LOCK_TIME)


@app.post(settings.scheduler_campaign)
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
        r.lpush('fila_campanhas', campanha_str)
        return {
            'message': f'Campanha para {platform} adicionada à fila com {actions} ações.',
            'content_id': content_id,
            'rate_limit': rate_limit
        }
    else:
        buffer_key = f'buffer:{platform}'
        r.rpush(buffer_key, campanha_str)
        return {
            'message': f'Campanha para {platform} guardada no buffer.',
            'content_id': content_id,
            'rate_limit': rate_limit
        }


@app.post(settings.alt_flag)
def alt_flag(flag: str):
    current = r.get(f'flag:{flag}')
    r.set(f'flag:{flag}', 0 if current == '1' else 1)


@app.get(settings.get_flag)
def get_flag(flag: str):
    return int(r.get(f'flag:{flag}') or 0)


@app.post(settings.scheduler_set_pause_time)
def set_pause_time(time: int):
    r.set('config:max_pause_time', time)


@app.get(settings.scheduler_get_pause_time)
def get_pause_time():
    return int(r.get('config:max_pause_time') or 64)


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


@app.post(settings.scheduler_post_campaign_result)
def post_campaign_result(
    platform: str,
    rate_limit: int,
    approved: int
):
    if r.get(f'flag:{settings.flag_threshold}') == '1':
        if approved == 1:
            increase_rate_limit(platform, rate_limit)
        elif approved == 0:
            decrease_rate_limit(platform, rate_limit)
    else:
        print(f'[{platform}] Flag de threshold desligada.')

    unlock(platform)


@app.get(settings.scheduler_get_campaign)
def get_campaign():
    if r.llen('fila_campanhas') == 0:
        possible_platforms = {}

        for plat in rate_limits.keys():
            buffer_key = f'buffer:{plat}'
            if r.llen(buffer_key) > 0 and not is_locked(plat):
                possible_platforms[plat] = rate_limits[plat]

        if possible_platforms:
            plats = list(possible_platforms.keys())

            if r.get(f'flag:{settings.flag_dynamic_distribution}') != '1':
                platform = random.choice(plats)
                print(f'Flag de dynamic distribution desligada.')
                print(f'Uma campanha para [{platform}] foi escolhida de forma aleatória.')
            else:
                weights = list(possible_platforms.values())
                platform = random.choices(plats, weights=weights, k=1)[0]
                print(f'Uma campanha para [{platform}] foi escolhida com base nos pesos {possible_platforms}')

            buffer_key = f'buffer:{platform}'
            campaign = r.lpop(buffer_key)
            lock(platform)
            return campaign
        else:
            print('Não existem campanhas em nenhum buffer.')

    campaign = r.lpop('fila_campanhas')
    if campaign:
        platform, _, _, _ = campaign.split(':')
        lock(platform)
        return campaign
    return None
