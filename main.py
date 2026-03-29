import redis
import subprocess
import requests
import time

FLAGS = [
    "flag:threshold",
    "flag:dynamic_distribution",
    "flag:jitter",
    "flag:circuit_breaker",
]

SCHEDULER_URL = "http://localhost:8000/start_campaign"
YOUTUBE_URL = "http://localhost:8001/api/youtube/get_likes"
INSTAGRAM_URL = "http://localhost:8002/api/instagram/get_likes"


def esperar_scheduler():
    url = "http://localhost:8000/docs"

    print("Aguardando scheduler ficar pronto...")

    while True:
        try:
            res = requests.get(url)
            if res.status_code == 200:
                print("Scheduler pronto!\n")
                break
        except:
            pass

        time.sleep(1)


def subir_docker(workers):
    print("\nParando containers antigos...")

    subprocess.run(
        ["docker", "compose", "down"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print(f"Subindo sistema com {workers} workers...")

    subprocess.Popen(
        ["docker", "compose", "up", "--build", "--scale", f"worker={workers}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("Aguardando serviços iniciarem...\n")


def escolher_content_id(plataforma):
    if plataforma == "youtube":
        prefixo = "youtube_video"
    else:
        prefixo = "instagram_video"

    print("\nEscolha o conteúdo:")
    for i in range(1, 6):
        print(f"{i} - {prefixo}_{i}")

    op = input("> ")

    try:
        op = int(op)
        if 1 <= op <= 5:
            return f"{prefixo}_{op}"
    except:
        pass

    print("Conteúdo inválido")
    return None


def enviar_campanha(plataforma, acoes, content_id):
    params = {
        "platform": plataforma,
        "actions": acoes,
        "content_id": content_id
    }

    response = requests.post(SCHEDULER_URL, params=params)

    if response.status_code == 200:
        print(f"\nCampanha enviada: {plataforma} ({acoes} ações)")
        print(f"Conteúdo: {content_id}")
        print(f"Resposta: {response.text}\n")
    else:
        print("Erro ao enviar campanha:", response.text)


def ver_likes():
    try:
        r_youtube = requests.get(YOUTUBE_URL)
        r_instagram = requests.get(INSTAGRAM_URL)

        data_youtube = r_youtube.json()
        data_instagram = r_instagram.json()

        total_youtube = data_youtube.get("total_likes", 0)
        total_instagram = data_instagram.get("total_likes", 0)

        videos_youtube = data_youtube.get("videos", {})
        videos_instagram = data_instagram.get("videos", {})

        print("\n=== TOTAL DE LIKES ===")
        print(f"YouTube:   {total_youtube}")
        print(f"Instagram: {total_instagram}")
        print("======================")

        print("\n--- YouTube por vídeo ---")
        for video_id, likes in videos_youtube.items():
            print(f"{video_id}: {likes}")

        print("\n--- Instagram por vídeo ---")
        for video_id, likes in videos_instagram.items():
            print(f"{video_id}: {likes}")

        print("")

    except Exception as e:
        print("Erro ao buscar likes:", e)


def mudar_flags():
    print("\n")
    for i, flag in enumerate(FLAGS, 1):
        print(f"{i} | {flag:<40} | {r.get(flag)}")
    print("0 | Sair")

    try:
        op = int(input("Qual flag deseja alternar? "))
    except ValueError: # tratamento de erros
        print("Opção inválida")
        return

    if op == 0:
        return

    if op < 1 or op > len(FLAGS): # tratamento de erros
        print("Opção inválida")
        return

    op -= 1

    if r.get(FLAGS[op]) == "0":
        r.set(FLAGS[op], 1)
    else:
        r.set(FLAGS[op], 0)


def menu():
    while True:
        print("\nEscolha:")
        print("1 - Adicionar likes no YouTube")
        print("2 - Adicionar likes no Instagram")
        print("3 - Ver likes")
        print("4 - Mudar flags")
        print("0 - Sair")

        op = input("> ")

        if op == "0":
            print("Encerrando...")
            break

        if op == "1":
            plataforma = "youtube"
        elif op == "2":
            plataforma = "instagram"
        elif op == "3":
            ver_likes()
            input("Aperte 'Enter' para continuar...")
            continue
        elif op == "4":
            mudar_flags()
            input("Aperte 'Enter' para continuar...")
            continue
        else:
            print("Opção inválida")
            continue

        try:
            acoes = int(input("Quantas ações? "))
        except:
            print("Número inválido")
            continue

        content_id = escolher_content_id(plataforma)
        if content_id is None:
            input("Aperte 'Enter' para continuar...")
            continue

        enviar_campanha(plataforma, acoes, content_id)
        input("Aperte 'Enter' para continuar...")


def main():
    try:
        workers = int(input("Quantos workers você quer? "))
    except:
        print("Número inválido")
        return

    subir_docker(workers)
    esperar_scheduler()

    global r
    r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    time.sleep(1)

    for flag in FLAGS:
        r.set(flag, 1)

    menu()


if __name__ == "__main__":
    main()