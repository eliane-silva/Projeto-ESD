import os
import subprocess
import sys
import time
import webbrowser

import requests
from dotenv import load_dotenv

load_dotenv()

SCHEDULER_HOME = os.getenv('SCHEDULER_HOME')
FRONTEND_URL = 'http://localhost:5173'


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


def subir_docker(total_de_workers):
    print('\nParando containers antigos...')
    subprocess.run(
        ['docker', 'compose', 'down'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(f'Subindo sistema com {total_de_workers} worker(s)...')
    subprocess.Popen(
        ['docker', 'compose', 'up', '--build', '--scale', f'worker={total_de_workers}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def esperar_servicos():
    print('Aguardando serviços iniciarem...', end='', flush=True)
    while True:
        try:
            if requests.get(SCHEDULER_HOME, timeout=2).status_code == 200:
                print(' OK')
                return
        except Exception:
            pass
        print('.', end='', flush=True)
        time.sleep(2)


def main():
    workers = ler_int('Quantos workers você quer? ', minimo=1)
    if workers is None:
        return

    subir_docker(workers)
    esperar_servicos()

    print(f'\nAbrindo frontend em {FRONTEND_URL}')
    webbrowser.open(FRONTEND_URL)

    print('Frontend aberto no navegador. Pressione Ctrl+C para derrubar o sistema.\n')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nDerrubando containers...')
        subprocess.run(
            ['docker', 'compose', 'down'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print('Sistema encerrado.')


if __name__ == '__main__':
    main()
