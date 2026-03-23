import subprocess
import requests
import time

SCHEDULER_URL = "http://localhost:8000/start_campaign"
YOUTUBE_URL = "http://localhost:8001/api/youtube/get_likes"
INSTAGRAM_URL = "http://localhost:8002/api/instagram/get_likes"


def esperar_scheduler():
    url = "http://localhost:8000/docs"  # ou qualquer endpoint

    print("Aguardando scheduler ficar pronto...")

    while True:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                print("Scheduler pronto!\n")
                break
        except:
            pass

        time.sleep(1)


def ver_likes():
    try:
        r_youtube = requests.get(YOUTUBE_URL)
        r_instagram = requests.get(INSTAGRAM_URL)
        likes_youtube = r_youtube.json()['likes']
        likes_instagram = r_instagram.json()['likes']

        print("\n=== TOTAL DE LIKES ===")
        print(f"YouTube:   {likes_youtube}")
        print(f"Instagram: {likes_instagram}")
        print("======================\n")

    except Exception as e:
        print("Erro ao buscar likes:", e)


def subir_docker(workers):
    print("\nParando containers antigos...")

    subprocess.run(
        ["docker", "compose", "down"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print(f"Subindo sistema com {workers} workers...")

    subprocess.Popen(
        ["docker", "compose", "up", "--build",
            f"--scale", f"worker={workers}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("Aguardando serviços iniciarem...\n")


def enviar_campanha(plataforma, acoes):
    params = {
        "platform": plataforma,
        "actions": acoes
    }

    response = requests.post(SCHEDULER_URL, params=params)

    if response.status_code == 200:
        print(f"\nCampanha enviada: {plataforma} ({acoes} ações)\n")
    else:
        print("Erro ao enviar campanha:", response.text)


def menu():
    while True:
        print("\nEscolha:")
        print("1 - Adicionar likes no YouTube")
        print("2 - Adicionar likes no Instagram")
        print("3 - Ver likes")
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
        else:
            print("Opção inválida")
            continue

        try:
            acoes = int(input("Quantas ações? "))
        except:
            print("Número inválido")
            continue

        enviar_campanha(plataforma, acoes)
        input("Aperte 'Enter' para continuar...")


def main():
    try:
        workers = int(input("Quantos workers você quer? "))
    except:
        print("Número inválido")
        return

    subir_docker(workers)
    esperar_scheduler()
    menu()


if __name__ == "__main__":
    main()
