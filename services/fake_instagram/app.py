from fastapi import FastAPI, HTTPException, Request
import redis
import os
import time

app = FastAPI(title="Fake Instagram")
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

@app.post("/api/instagram/like")
def instagram_like(request: Request):
    ip = request.client.host
    key = f"limit:instagram:{ip}"
    
    requests = r.incr(key)
    if requests == 1:
        r.expire(key, 60)
        
    if requests > 15: # Instagram mais rigoroso
        raise HTTPException(status_code=429, detail="Instagram: Too Many Requests")
        
    time.sleep(0.1)
    return {"status": "success", "platform": "instagram", "requests": requests}