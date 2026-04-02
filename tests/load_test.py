from locust import HttpUser, task, between, events
import random

class CampaignUser(HttpUser):
    # Tempo de espera entre tarefas (1 a 2 segundos)
    wait_time = between(1, 2)
    
    # URL base do Scheduler (ajustar se necessário)
    host = "http://localhost:8000"

    @task(3)
    def start_campaign_youtube(self):
        """Simula a criação de uma campanha para o YouTube"""
        content_id = f"youtube_video_{random.randint(1, 5)}"
        actions = random.randint(10, 100)
        
        self.client.post(
            f"/start_campaign?platform=youtube&actions={actions}&content_id={content_id}",
            name="/start_campaign [youtube]"
        )

    @task(3)
    def start_campaign_instagram(self):
        """Simula a criação de uma campanha para o Instagram"""
        content_id = f"instagram_video_{random.randint(1, 5)}"
        actions = random.randint(10, 100)
        
        self.client.post(
            f"/start_campaign?platform=instagram&actions={actions}&content_id={content_id}",
            name="/start_campaign [instagram]"
        )

    @task(1)
    def check_health(self):
        """Simula um usuário apenas verificando se o scheduler está ativo"""
        self.client.get("/docs", name="Health Check (Docs)")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Iniciando teste de carga...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Teste de carga finalizado.")
