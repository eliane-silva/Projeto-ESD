from fastapi import FastAPI, HTTPException, Request
import redis
import os
import time
import uuid

app = FastAPI(title="Fake Instagram")
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

LIMIT = 30
WINDOW = 60


@app.post("/api/instagram/like")
def instagram_like(request: Request):
    ip = request.client.host
    key = f"limit:instagram:{ip}"

    now = time.time()

    r.zremrangebyscore(key, 0, now - WINDOW)

    current = r.zcard(key)

    if current >= LIMIT:
        raise HTTPException(
            status_code=429, detail="YouTube: Too Many Requests")

    r.zadd(key, {str(uuid.uuid4()): now})
    r.expire(key, WINDOW)

    r.incr("likes:instagram")
    time.sleep(0.1)
    return {"status": "success", "platform": "instagram", "requests": current + 1, "total_likes": r.get("likes:instagram")}

@app.get("/api/instagram/get_likes")
def get_likes():
    total = r.get("likes:instagram") or 0

    return {
        "likes": int(total),
    }
