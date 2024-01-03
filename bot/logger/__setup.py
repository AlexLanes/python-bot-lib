# std
import logging
from sys import exc_info
from datetime import datetime, timedelta
# interno
import bot
from bot.util import info_stack


NOME_ARQUIVO = ".log"
CAMINHO_PASTA_LOGS = "./logs"
FORMATO_NOME_LOG = "%Y-%m-%dT%H-%M-%S.log"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | id(%(process)d) | level(%(levelname)s) | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    filename=NOME_ARQUIVO,
    encoding="utf-8",
    filemode="w"
)


def debug (mensagem: str) -> None:
    """Log nível 'DEBUG'"""
    logging.debug(f"arquivo({ info_stack(2).nome }) | função({ info_stack(2).funcao }) | linha({ info_stack(2).linha }) | { mensagem }")

    
def informar (mensagem: str) -> None:
    """Log nível 'INFO'"""
    logging.info(f"arquivo({ info_stack(2).nome }) | função({ info_stack(2).funcao }) | linha({ info_stack(2).linha }) | { mensagem }")


def alertar (mensagem: str) -> None:
    """Log nível 'WARNING'"""
    logging.warning(f"arquivo({ info_stack(2).nome }) | função({ info_stack(2).funcao }) | linha({ info_stack(2).linha }) | { mensagem }")


def erro (mensagem: str) -> None:
    """Log nível 'ERROR'"""
    logging.error(f"arquivo({ info_stack(2).nome }) | função({ info_stack(2).funcao }) | linha({ info_stack(2).linha }) | { mensagem }", exc_info=exc_info())


def salvar_log (caminho: bot.tipagem.caminho = CAMINHO_PASTA_LOGS) -> None:
    """Salvar o arquivo log para a pasta informada
    - o nome do arquivo é o datetime atual"""
    caminho = bot.windows.path.abspath(caminho)
    if not bot.windows.path.exists(caminho):
        bot.windows.criar_pasta(caminho)
    nome = datetime.now().strftime(FORMATO_NOME_LOG)
    bot.windows.copiar_arquivo(NOME_ARQUIVO, f"{ caminho }/{ nome }")


def limpar_logs (limite = timedelta(weeks=2)) -> None:
    """Limpar os logs que ultrapassaram a data limite
    - espera que os logs tenham o nome no formato `FORMATO_NOME_LOG`"""
    agora = datetime.now().replace(microsecond=0)
    for arquivo in bot.windows.listar_diretorio(CAMINHO_PASTA_LOGS).arquivos:
        nome = bot.windows.path.basename(arquivo)
        data = datetime.strptime(nome, FORMATO_NOME_LOG)
        diferenca = agora - data
        if diferenca > limite: bot.windows.apagar_arquivo(arquivo)


__all__ = [
    "erro",
    "debug", 
    "alertar",
    "informar",
    "salvar_log",
    "limpar_logs",
    "NOME_ARQUIVO",
    "CAMINHO_PASTA_LOGS"
]
