from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from config import settings

# Parâmetros de throttling
LIMIT = 120
WINDOW = 1

# Conteúdos da plataforma
videos = {
    f'instagram_video_{i}': {'likes': 0}
    for i in range(1, 6)
}
requests_por_ip = {}

app = FastAPI(title='Fake Instagram')
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get(settings.instagram_list_videos)
def list_videos():
    return {
        'platform': 'instagram',
        'videos': [
            {'video_id': video_id, 'likes': data['likes']}
            for video_id, data in videos.items()
        ]
    }


@app.post(settings.instagram_like_video)
def like_video(
    request: Request,
    video_id: str = Query(..., description='Identificador do conteúdo')
):
    ip = request.client.host
    now = time.time()

    if video_id not in videos:
        raise HTTPException(
            status_code=404, detail='Instagram: conteúdo não encontrado')

    if ip not in requests_por_ip:
        requests_por_ip[ip] = []

    requests_por_ip[ip] = [t for t in requests_por_ip[ip] if t > now - WINDOW]
    current = len(requests_por_ip[ip])

    if current >= LIMIT:
        raise HTTPException(
            status_code=429, detail='Instagram: Too Many Requests')

    requests_por_ip[ip].append(now)
    videos[video_id]['likes'] += 1

    time.sleep(0.1)

    return {
        'status': 'success',
        'platform': 'instagram',
        'video_id': video_id,
        'requests': current + 1,
        'likes_for_video': videos[video_id]['likes'],
        'total_likes': sum(video['likes'] for video in videos.values())
    }


@app.get(settings.instagram_get_likes)
def get_likes(video_id: str | None = None):
    if video_id is not None:
        if video_id not in videos:
            raise HTTPException(
                status_code=404, detail='Instagram: conteúdo não encontrado')
        return {
            'platform': 'instagram',
            'video_id': video_id,
            'likes': videos[video_id]['likes']
        }

    return {
        'platform': 'instagram',
        'total_likes': sum(video['likes'] for video in videos.values()),
        'videos': {
            video_id: data['likes'] for video_id, data in videos.items()
        }
    }
