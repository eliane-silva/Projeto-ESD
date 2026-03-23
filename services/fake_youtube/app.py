from fastapi import FastAPI, HTTPException, Request
import redis
import os
import time
import uuid

app = FastAPI(title="Fake YouTube")
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

LIMIT = 30
WINDOW = 60


@app.post("/api/youtube/like")
def youtube_like(request: Request):
    ip = request.client.host
    key = f"limit:youtube:{ip}"

    now = time.time()

    r.zremrangebyscore(key, 0, now - WINDOW)

    current = r.zcard(key)

    if current >= LIMIT:
        raise HTTPException(
            status_code=429, detail="YouTube: Too Many Requests")

    r.zadd(key, {str(uuid.uuid4()): now})
    r.expire(key, WINDOW)

    r.incr("likes:youtube")
    time.sleep(0.1)  # Simula latência
    return {"status": "success", "platform": "youtube", "requests": current + 1, "total_likes": r.get("likes:youtube")}


@app.get("/api/youtube/get_likes")
def get_likes():
    total = r.get("likes:youtube") or 0

    return {
        "likes": int(total),
    }
