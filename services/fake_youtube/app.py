from fastapi import FastAPI, HTTPException, Request, Query
import os
import time

# URLs da API
YOUTUBE_LIST_VIDEOS = os.getenv("YOUTUBE_LIST_VIDEOS")
YOUTUBE_LIKE_VIDEO = os.getenv("YOUTUBE_LIKE_VIDEO")
YOUTUBE_GET_LIKES = os.getenv("YOUTUBE_GET_LIKES")

# Parâmetros de throttling
LIMIT = 1
WINDOW = 5

# Conteúdos da plataforma
videos = {
    f'youtube_video_{i}': {'likes': 0}
    for i in range(1, 6)
}
requests_por_ip = {}

app = FastAPI(title='Fake YouTube')


@app.get(YOUTUBE_LIST_VIDEOS)
def list_videos():
    return {
        'platform': 'youtube',
        'videos': [
            {'video_id': video_id, 'likes': data['likes']}
            for video_id, data in videos.items()
        ]
    }


@app.post(YOUTUBE_LIKE_VIDEO)
def like_video(
    request: Request,
    video_id: str = Query(..., description='Identificador do conteúdo')
):
    ip = request.client.host
    now = time.time()

    if video_id not in videos:
        raise HTTPException(
            status_code=404, detail='YouTube: conteúdo não encontrado')

    if ip not in requests_por_ip:
        requests_por_ip[ip] = []

    requests_por_ip[ip] = [t for t in requests_por_ip[ip] if t > now - WINDOW]
    current = len(requests_por_ip[ip])

    if current >= LIMIT:
        raise HTTPException(
            status_code=429, detail='YouTube: Too Many Requests')

    requests_por_ip[ip].append(now)
    videos[video_id]['likes'] += 1

    time.sleep(0.1)

    return {
        'status': 'success',
        'platform': 'youtube',
        'video_id': video_id,
        'requests': current + 1,
        'likes_for_video': videos[video_id]['likes'],
        'total_likes': sum(video['likes'] for video in videos.values())
    }


@app.get(YOUTUBE_GET_LIKES)
def get_likes(video_id: str | None = None):
    if video_id is not None:
        if video_id not in videos:
            raise HTTPException(
                status_code=404, detail='YouTube: conteúdo não encontrado')
        return {
            'platform': 'youtube',
            'video_id': video_id,
            'likes': videos[video_id]['likes']
        }

    return {
        'platform': 'youtube',
        'total_likes': sum(video['likes'] for video in videos.values()),
        'videos': {
            video_id: data['likes'] for video_id, data in videos.items()
        }
    }
