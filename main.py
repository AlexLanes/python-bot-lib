# std
from time import sleep
# interno
import bot


def main():
    """Fluxo principal"""
    pass


if __name__ == "__main__":
    try: main()
    except TimeoutError: bot.logger.erro("Erro de timeout na espera de alguma condição/elemento/janela")
    except AssertionError: bot.logger.erro("Erro de validação pré-execução de algum passo no fluxo")
    except Exception: bot.logger.erro("Erro inesperado no fluxo")
    finally: bot.logger.salvar_log(); bot.logger.limpar_logs()
