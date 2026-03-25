from fastapi import FastAPI, HTTPException, Request
import time

app = FastAPI(title="Fake Instagram")

LIMIT = 120
WINDOW = 1

# Estruturas em memória
requests_por_ip = {}   # ip -> [timestamps]
total_likes = 0


@app.post("/api/instagram/like")
def instagram_like(request: Request):
    global total_likes

    ip = request.client.host
    now = time.time()

    if ip not in requests_por_ip:
        requests_por_ip[ip] = []

    # remove requisições antigas
    requests_por_ip[ip] = [
        t for t in requests_por_ip[ip] if t > now - WINDOW
    ]

    current = len(requests_por_ip[ip])

    if current >= LIMIT:
        raise HTTPException(
            status_code=429, detail="Instagram: Too Many Requests"
        )

    # adiciona nova requisição
    requests_por_ip[ip].append(now)

    total_likes += 1

    time.sleep(0.1)

    return {
        "status": "success",
        "platform": "instagram",
        "requests": current + 1,
        "total_likes": total_likes
    }


@app.get("/api/instagram/get_likes")
def get_likes():
    return {
        "likes": total_likes
    }