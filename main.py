import os
import subprocess
import requests
import time
from dotenv import load_dotenv


# Carregando variáveis do ambiente
load_dotenv()

SCHEDULER_HOME = os.getenv('SCHEDULER_HOME')
SCHEDULER_CAMPAIGN = os.getenv('SCHEDULER_CAMPAIGN')
SCHEDULER_SET_PAUSE_TIME = os.getenv('SCHEDULER_SET_PAUSE_TIME')
SCHEDULER_GET_PAUSE_TIME = os.getenv('SCHEDULER_GET_PAUSE_TIME')

ALT_FLAG = os.getenv('ALT_FLAG')
GET_FLAG = os.getenv('GET_FLAG')
FLAGS_TAGS = os.getenv('FLAGS').split(',')
FLAGS = [os.getenv(tag) for tag in FLAGS_TAGS]

YOUTUBE_LIST_VIDEOS = os.getenv('YOUTUBE_LIST_VIDEOS')
YOUTUBE_GET_LIKES = os.getenv('YOUTUBE_GET_LIKES')
INSTAGRAM_LIST_VIDEOS = os.getenv('INSTAGRAM_LIST_VIDEOS')
INSTAGRAM_GET_LIKES = os.getenv('INSTAGRAM_GET_LIKES')
TEMPLATE_METRICS_URL = os.getenv('METRICS_URL')


# Funções de preparação do ambiente
def subir_docker(total_de_workers):
    print('\nParando containers antigos...')

    subprocess.run(
        ['docker', 'compose', 'down'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print(f'Subindo sistema com {total_de_workers} workers...')

    subprocess.Popen(
        ['docker', 'compose', 'up', '--build',
            '--scale', f'worker={total_de_workers}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def esperar_scheduler():
    print('Aguardando serviços iniciarem...')

    while True:
        try:
            res = requests.get(SCHEDULER_HOME)
            if res.status_code == 200:
                print('Serviços iniciados com sucesso.\n')
                break
        except:
            pass

        time.sleep(1)


# Funções do menu principal
def ler_int(mensagem, minimo=None):
    valor_str = input(mensagem).strip()

    try:
        valor = int(valor_str)
    except ValueError:
        print('Número inválido')
        return None

    if minimo is not None and valor < minimo:
        print(f'O valor deve ser maior ou igual a {minimo}')
        return None

    return valor


def enviar_campanha(plataforma):
    def escolher_content_id(plataforma):
        if plataforma == 'youtube':
            videos = requests.get(YOUTUBE_LIST_VIDEOS).json().get('videos')
        elif plataforma == 'instagram':
            videos = requests.get(INSTAGRAM_LIST_VIDEOS).json().get('videos')

        video_ids = [video['video_id'] for video in videos]

        print('\nEscolha o conteúdo:')
        for i, video_id in enumerate(video_ids, 1):
            print(f'{i} - {video_id}')

        op = input('> ')

        try:
            op = int(op)
            if 1 <= op <= 5:
                return video_ids[op - 1]
        except:
            pass

        print('Conteúdo inválido')
        return None

    acoes = ler_int('Quantas ações? ', minimo=1)
    if acoes is None:
        return

    content_id = escolher_content_id(plataforma)
    if content_id is None:
        return

    params = {
        'platform': plataforma,
        'actions': acoes,
        'content_id': content_id
    }

    response = requests.post(SCHEDULER_CAMPAIGN, params=params)

    if response.status_code == 200:
        print(f'\nCampanha enviada: {plataforma} ({acoes} ações)')
        print(f'Conteúdo: {content_id}')
        print(f'Resposta: {response.text}\n')
    else:
        print('Erro ao enviar campanha:', response.text)


def ver_likes():
    try:
        r_youtube = requests.get(YOUTUBE_GET_LIKES)
        r_instagram = requests.get(INSTAGRAM_GET_LIKES)

        data_youtube = r_youtube.json()
        data_instagram = r_instagram.json()

        total_youtube = data_youtube.get('total_likes', 0)
        total_instagram = data_instagram.get('total_likes', 0)

        videos_youtube = data_youtube.get('videos', {})
        videos_instagram = data_instagram.get('videos', {})

        print('\n=== TOTAL DE LIKES ===')
        print(f'YouTube:   {total_youtube}')
        print(f'Instagram: {total_instagram}')
        print('======================')

        print('\n--- YouTube por vídeo ---')
        for video_id, likes in videos_youtube.items():
            print(f'{video_id}: {likes}')

        print('\n--- Instagram por vídeo ---')
        for video_id, likes in videos_instagram.items():
            print(f'{video_id}: {likes}')

        print()

    except Exception as e:
        print('Erro ao buscar likes:', e)


def mudar_flags():
    print('\n')
    for i, flag in enumerate(FLAGS, 1):
        print(f'{i} | {flag:<40} | {requests.get(f"{GET_FLAG}?flag={flag}").text}')
    print('0 | Sair')

    try:
        op = int(input('Qual flag deseja alternar? '))
    except ValueError:  # tratamento de erros
        print('Opção inválida')
        return

    if op == 0:
        return

    if op < 1 or op > len(FLAGS):  # tratamento de erros
        print('Opção inválida')
        return

    op -= 1

    requests.post(f'{ALT_FLAG}?flag={FLAGS[op]}')


def configurar_teto():
    atual = requests.get(SCHEDULER_GET_PAUSE_TIME).text
    print(f'\nTeto atual do circuit breaker: {atual}s')

    try:
        novo = int(input('Novo valor em segundos: '))
        if novo <= 0:
            print('Valor deve ser maior que zero')
            return
    except ValueError:
        print('Valor inválido')
        return

    requests.post(f'{SCHEDULER_SET_PAUSE_TIME}?time={novo}')
    print(f'Teto atualizado para {novo}s')

def ver_metricas():
    plataformas = ['youtube', 'instagram']
    print()
    
    for plataforma in plataformas:
        try:
            response = requests.get(TEMPLATE_METRICS_URL.format(plataforma=plataforma))
            if response.status_code == 200:
                data = response.json()
                print(f"\nMétricas para {plataforma.capitalize()}:")
                print(f"Total de ações: {data['total']}")
                print(f"Ações bem-sucedidas: {data['success']}")
                print(f"Ações com erro: {data['errors']}")
                print(f"Ações bloqueadas: {data['blocked']}")
                print(f"Taxa de sucesso: {data['success_rate']:.2%}")
                print(f"Taxa de erro: {data['error_rate']:.2%}")
                print(f"Taxa de bloqueio: {data['block_rate']:.2%}\n")
            else:
                print('Erro ao buscar métricas:', response.text)
        except Exception as e:
            print('Erro ao conectar com o serviço de monitoramento:', e)


# Menu principal
def menu():
    while True:
        print('\nEscolha:')
        print('1 - Adicionar likes no YouTube')
        print('2 - Adicionar likes no Instagram')
        print('3 - Ver likes')
        print('4 - Mudar flags')
        print('5 - Configurar teto do circuit breaker')
        print('6 - Ver métricas de monitoramento (banco de dados)')
        print('0 - Sair')

        op = input('> ')

        if op == '0':
            print('Encerrando...')
            break

        if op == '1':
            plataforma = 'youtube'
            enviar_campanha(plataforma)
            input('Aperte "Enter" para continuar...')
        elif op == '2':
            plataforma = 'instagram'
            enviar_campanha(plataforma)
            input('Aperte "Enter" para continuar...')
        elif op == '3':
            ver_likes()
            input('Aperte "Enter" para continuar...')
            continue
        elif op == '4':
            mudar_flags()
            input('Aperte "Enter" para continuar...')
            continue
        elif op == '5':
            configurar_teto()
            input('Aperte "Enter" para continuar...')
            continue
        elif op == '6':
            ver_metricas()
            input('Aperte "Enter" para continuar...')
            continue
        else:
            print('Opção inválida')
            continue


# Corpo principal do programa
def main():
    workers = ler_int('Quantos workers você quer? ', minimo=1)
    if workers is None:
        return

    subir_docker(workers)
    esperar_scheduler()

    menu()


if __name__ == '__main__':
    main()
