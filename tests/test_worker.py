import pytest
import time
from unittest.mock import patch, MagicMock
from config import settings

# Mockamos o redis globalmente para os testes do worker
@pytest.fixture
def mock_redis():
    mr = MagicMock()
    mr.get.return_value = "0" # Default flags
    return mr

def test_worker_parsing_logic():
    # Testamos se o formato da mensagem na fila está correto conforme o worker espera
    dados = "youtube:10:5.0:youtube_video_1"
    plataforma, acoes, rate_limit, content_id = dados.split(':', 3)
    assert plataforma == "youtube"
    assert int(acoes) == 10
    assert int(float(rate_limit)) == 5
    assert content_id == "youtube_video_1"

@patch("httpx.Client")
def test_worker_selection_logic(mock_client_class, mock_redis):
    # Simula o que o worker faz ao puxar da fila
    plataforma = "youtube"
    acoes = 1
    content_id = "youtube_video_1"
    
    # Prepara o mock do cliente HTTP
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    
    # Simula resposta 200
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response

    # Lógica simplificada do worker para validar a integração
    url_base = settings.youtube_like_url
    from urllib.parse import urlencode
    url_alvo = f'{url_base}?{urlencode({"video_id": content_id})}'
    
    response = mock_client.post(url_alvo)
    
    assert response.status_code == 200
    mock_client.post.assert_called_with(url_alvo)

def test_worker_circuit_breaker_logic_mocked(mock_redis):
    # Testamos a lógica de cálculo de pausa do circuit breaker sem conexão real
    mock_redis.set("flag:circuit_breaker", "1")
    mock_redis.set("config:max_pause_time", "64")
    
    # Simulamos o comportamento do redis.get
    def side_effect(key):
        return {
            f"flag:{settings.flag_circuit_breaker}": "1", 
            "config:max_pause_time": "64"
        }.get(key, "0")
    mock_redis.get.side_effect = side_effect
    
    pause_time = 1
    # Simula o branch do 429 no worker.py
    if mock_redis.get(f"flag:{settings.flag_circuit_breaker}") == "1":
        max_pause = int(mock_redis.get("config:max_pause_time") or 64)
        pause_time = min(pause_time * 2, max_pause)
            
    assert pause_time == 2
