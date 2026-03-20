from fastapi import FastAPI, HTTPException, Request
import redis
import os
import time

app = FastAPI(title="Fake YouTube")
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

@app.post("/api/youtube/like")
def youtube_like(request: Request):
    ip = request.client.host
    key = f"limit:youtube:{ip}"
    
    requests = r.incr(key)
    if requests == 1:
        r.expire(key, 60) # A chave some sozinha em 60s
        
    if requests > 30:
        raise HTTPException(status_code=429, detail="YouTube: Too Many Requests")
        
    time.sleep(0.1) # Simula latência
    return {"status": "success", "platform": "youtube", "requests": requests}