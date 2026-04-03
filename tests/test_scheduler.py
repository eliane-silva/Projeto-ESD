import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from config import settings

# Mock global para o Redis
mock_redis = MagicMock()

# Precisamos mockar o Redis e o requests ANTES de importar o app do scheduler
with patch("redis.from_url", return_value=mock_redis), \
     patch("requests.get"), \
     patch("requests.post"):
    from services.scheduler.scheduler import app, VALID_CONTENT
    
    # Popula VALID_CONTENT manualmente para os testes
    VALID_CONTENT['youtube'] = {'youtube_video_1', 'youtube_video_2'}
    VALID_CONTENT['instagram'] = {'instagram_video_1'}

@pytest.fixture(autouse=True)
def mock_requests():
    """Mock global para todas as chamadas de rede do requests nos testes."""
    with patch("requests.get") as m_get, patch("requests.post") as m_post:
        yield m_get, m_post

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def setup_function():
    # Limpa o mock antes de cada teste
    mock_redis.reset_mock()
    # Simula o comportamento do flushdb e garante que get retorne None por padrão
    mock_redis.flushdb.return_value = True
    mock_redis.get.return_value = None

def test_lock_e_buffer_de_campanhas(client):
    # Dicionário para simular o estado do Redis
    redis_state = {}
    
    def mock_get(key):
        return redis_state.get(key)
        
    def mock_set(key, value, **kwargs):
        if kwargs.get('nx') and key in redis_state:
            return False
        redis_state[key] = str(value)
        return True

    mock_redis.get.side_effect = mock_get
    mock_redis.set.side_effect = mock_set
    
    # Envia a primeira campanha para o YouTube (deve ir para a fila e criar o lock pois is_locked e False)
    response1 = client.post(f"{settings.scheduler_campaign}?platform=youtube&actions=10&content_id=youtube_video_1")
    assert response1.status_code == 200
    assert "adicionada à fila" in response1.json()["message"]
    
    # Verifica se o lock foi tentado
    mock_redis.set.assert_any_call("lock:youtube", 1, nx=True, ex=120)

    # Envia a segunda campanha para o YouTube (deve ir para o buffer pois o lock existe)
    response2 = client.post(f"{settings.scheduler_campaign}?platform=youtube&actions=5&content_id=youtube_video_2")
    assert response2.status_code == 200
    assert "guardada no buffer" in response2.json()["message"]
    
    # Verifica se tentou enfileirar (lpush) e buferizar (rpush)
    mock_redis.lpush.assert_called()
    mock_redis.rpush.assert_called()

def test_throttle_diminui_rate_limit(client):
    # Simula a flag ligada no Redis
    def side_effect(key):
        if settings.flag_threshold in key:
            return '1'
        return None
    mock_redis.get.side_effect = side_effect
    
    # Chama a rota de resultado de campanha informando que rate_limit 120 foi rejeitado (approved=0)
    response = client.post(f"{settings.scheduler_post_campaign_result}?platform=youtube&rate_limit=120&approved=0")
    assert response.status_code == 200
    
    # A velocidade atual deve cair (a lógica do seu código reduz para algo próximo da metade)
    # Como safer_rate_limits inicial é 0, a nova velocidade será 120 - (120 - 0) / 2 = 60
    from services.scheduler.scheduler import rate_limits
    assert rate_limits['youtube'] == 60