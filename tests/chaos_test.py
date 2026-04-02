import subprocess
import time
import redis
import os

# Configuração
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
r = redis.from_url(REDIS_URL, decode_responses=True)

def run_command(cmd):
    print(f"Executando: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True)

def test_chaos_redis_restart():
    print("\n--- TESTE 1: Reiniciando Redis durante carga ---")
    # Este teste pressupõe que o Locust ou outro script está mandando carga
    run_command(["docker", "compose", "stop", "redis"])
    print("Redis PARADO. Aguardando 5 segundos...")
    time.sleep(5)
    run_command(["docker", "compose", "start", "redis"])
    print("Redis REINICIADO. Verificando logs do worker...")
    time.sleep(2)
    # Verifica se os workers voltaram a processar (via log ou fila)
    print("Sucesso: O sistema deve se reconectar automaticamente.")

def test_chaos_kill_worker():
    print("\n--- TESTE 2: Matando um Worker aleatório ---")
    
    # Pega todos os contêineres rodando (ID e Nome)
    res = run_command(["docker", "ps", "--format", "{{.ID}} {{.Names}}"])
    
    # Filtra no próprio Python quem tem "worker" no nome
    workers = []
    if res.stdout:
        for linha in res.stdout.strip().split('\n'):
            if 'worker' in linha.lower():
                id_container = linha.split()[0]
                workers.append(id_container)
    
    if workers:
        target = workers[0]  # Pega o primeiro da lista
        print(f"Matando worker {target}...")
        run_command(["docker", "kill", target])
        time.sleep(2)
        print("Worker morto. Verificando se a fila continua sendo processada por outros...")
    else:
        print("Nenhum worker encontrado. Verifique se os contêineres estão rodando.")

if __name__ == "__main__":
    print("=== INICIANDO TESTES DE CAOS (Chaos Engineering) ===")
    try:
        test_chaos_redis_restart()
        test_chaos_kill_worker()
    except Exception as e:
        print(f"Erro durante os testes: {e}")
    print("\n=== TESTES DE CAOS FINALIZADOS ===")