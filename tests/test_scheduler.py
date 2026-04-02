import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Precisamos mockar o Redis ANTES de importar o app do scheduler
# porque o scheduler.py cria a conexão no nível do módulo.

mock_redis = MagicMock()

with patch("redis.from_url", return_value=mock_redis):
    from services.scheduler.scheduler import app

client = TestClient(app)

def setup_function():
    # Limpa o mock antes de cada teste
    mock_redis.reset_mock()
    # Simula o comportamento do flushdb
    mock_redis.flushdb.return_value = True

def test_lock_e_buffer_de_campanhas():
    # Configura o mock para simular o comportamento de adquirir lock (set nx=True)
    # Na primeira vez (lock:youtube), retorna True
    # Na segunda vez (lock:youtube), retorna False
    mock_redis.set.side_effect = [True, False]
    
    # Envia a primeira campanha para o YouTube (deve ir para a fila e criar o lock)
    response1 = client.post("/start_campaign?platform=youtube&actions=10&content_id=youtube_video_1")
    assert response1.status_code == 200
    assert "adicionada à fila" in response1.json()["message"]
    
    # Verifica se o lock foi tentado
    mock_redis.set.assert_any_call("lock:youtube", 1, nx=True, ex=120)

    # Envia a segunda campanha para o YouTube (deve ir para o buffer pois o lock existe)
    response2 = client.post("/start_campaign?platform=youtube&actions=5&content_id=youtube_video_2")
    assert response2.status_code == 200
    assert "guardada no buffer" in response2.json()["message"]
    
    # Verifica se tentou enfileirar (lpush) e buferizar (rpush)
    mock_redis.lpush.assert_called()
    mock_redis.rpush.assert_called()

def test_throttle_diminui_rate_limit():
    # Simula a flag ligada
    mock_redis.get.return_value = '1' 
    
    # Chama a rota de throttle informando que 120 falhou
    response = client.post("/throttle?platform=youtube&rejected_rate_limit=120")
    assert response.status_code == 200
    
    # A velocidade atual deve cair (a lógica do seu código reduz para algo próximo da metade)
    # Como safer_rate_limits inicial é 0, a nova velocidade será 120 - (120 - 0) / 2 = 60
    from services.scheduler.scheduler import rate_limits
    assert rate_limits['youtube'] == 60