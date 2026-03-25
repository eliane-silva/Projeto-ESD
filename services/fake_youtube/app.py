from fastapi import FastAPI, HTTPException, Request
import time

app = FastAPI(title="Fake YouTube")

LIMIT = 1
WINDOW = 5

# Estruturas em memória
requests_por_ip = {}   # ip -> [timestamps]
total_likes = 0


@app.post("/api/youtube/like")
def youtube_like(request: Request):
    global total_likes

    ip = request.client.host
    now = time.time()

    if ip not in requests_por_ip:
        requests_por_ip[ip] = []

    # Remove requisições fora da janela
    requests_por_ip[ip] = [
        t for t in requests_por_ip[ip] if t > now - WINDOW
    ]

    current = len(requests_por_ip[ip])

    if current >= LIMIT:
        raise HTTPException(
            status_code=429, detail="YouTube: Too Many Requests"
        )

    # Adiciona nova requisição
    requests_por_ip[ip].append(now)

    total_likes += 1

    time.sleep(0.1)  # simula latência

    return {
        "status": "success",
        "platform": "youtube",
        "requests": current + 1,
        "total_likes": total_likes
    }


@app.get("/api/youtube/get_likes")
def get_likes():
    return {
        "likes": total_likes
    }