# std
from time import sleep
from multiprocessing.context import TimeoutError as Timeout
# interno
import bot


@bot.util.decoradores.setar_timeout(300)
def main():
    """Fluxo principal"""
    pass


if __name__ == "__main__":
    try: 
        main()
    except Timeout:
        bot.logger.erro("Fluxo demorou mais tempo que o esperado em sua execução")
    except Exception: 
        bot.logger.erro("Erro inesperado no fluxo")
