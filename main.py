# std
from time import sleep
# interno
import bot


def main():
    """Fluxo principal"""
    pass


if __name__ == "__main__":
    try: main()
    except Exception: bot.logger.erro("Erro inesperado no fluxo")
    # finally: bot.logger.salvar_log(); bot.logger.limpar_logs()
