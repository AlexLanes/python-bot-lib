# std
from time import sleep
# interno
import bot


@bot.util.decoradores.tempo_execucao
def main():
    """Fluxo principal"""
    from queue import PriorityQueue
    pass


if __name__ == "__main__":
    try: 
        main()
    except Exception: 
        bot.logger.erro("Erro inesperado no fluxo")
