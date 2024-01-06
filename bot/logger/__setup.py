# std
import logging
from sys import exc_info
from datetime import datetime, timedelta
# interno
import bot
from bot.util import obter_info_stack
from bot.windows import diretorio_execucao


NOME_ARQUIVO_LOG = ".log"
CAMINHO_PASTA_LOGS = "./logs"
FORMATO_NOME_LOG = "%Y-%m-%dT%H-%M-%S.log"
DIRETORIO_EXECUCAO = diretorio_execucao().caminho


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | id(%(process)d) | level(%(levelname)s) | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    filename=NOME_ARQUIVO_LOG,
    encoding="utf-8",
    filemode="w"
)


def debug (mensagem: str) -> None:
    """Log nível 'DEBUG'"""
    stack = obter_info_stack(2)
    caminho = '\\'.join([ stack.caminho.replace(DIRETORIO_EXECUCAO, ''), stack.nome ]).lstrip("\\")
    logging.debug(f"arquivo({ caminho }) | função({ stack.funcao }) | linha({ stack.linha }) | { mensagem }")

    
def informar (mensagem: str) -> None:
    """Log nível 'INFO'"""
    stack = obter_info_stack(2)
    caminho = '\\'.join([ stack.caminho.replace(DIRETORIO_EXECUCAO, ''), stack.nome ]).lstrip("\\")
    logging.info(f"arquivo({ caminho }) | função({ stack.funcao }) | linha({ stack.linha }) | { mensagem }")


def alertar (mensagem: str) -> None:
    """Log nível 'WARNING'"""
    stack = obter_info_stack(2)
    caminho = '\\'.join([ stack.caminho.replace(DIRETORIO_EXECUCAO, ''), stack.nome ]).lstrip("\\")
    logging.warning(f"arquivo({ caminho }) | função({ stack.funcao }) | linha({ stack.linha }) | { mensagem }")


def erro (mensagem: str) -> None:
    """Log nível 'ERROR'"""
    stack = obter_info_stack(2)
    caminho = '\\'.join([ stack.caminho.replace(DIRETORIO_EXECUCAO, ''), stack.nome ]).lstrip("\\")
    logging.error(f"arquivo({ caminho }) | função({ stack.funcao }) | linha({ stack.linha }) | { mensagem }", exc_info=exc_info())


def salvar_log (caminho: bot.tipagem.caminho = CAMINHO_PASTA_LOGS) -> None:
    """Salvar o arquivo log na pasta informada
    - o nome do arquivo é o datetime atual"""
    nome = datetime.now().strftime(FORMATO_NOME_LOG)
    caminho = bot.windows.path.abspath(caminho)
    if not bot.windows.path.exists(caminho): bot.windows.criar_pasta(caminho)
    bot.windows.copiar_arquivo(NOME_ARQUIVO_LOG, f"{ caminho }/{ nome }")


def limpar_logs (caminho: bot.tipagem.caminho = CAMINHO_PASTA_LOGS, limite = timedelta(weeks=2)) -> None:
    """Limpar os logs que ultrapassaram a data limite
    - espera que os logs tenham o nome no formato `FORMATO_NOME_LOG`"""
    agora = datetime.now().replace(microsecond=0)
    caminho = bot.windows.path.abspath(caminho)
    if not bot.windows.path.exists(caminho): return
    for arquivo in bot.windows.listar_diretorio(caminho).arquivos:
        nome = bot.windows.path.basename(arquivo)
        data = datetime.strptime(nome, FORMATO_NOME_LOG)
        if agora - data > limite: bot.windows.apagar_arquivo(arquivo)


__all__ = [
    "erro",
    "debug", 
    "alertar",
    "informar",
    "salvar_log",
    "limpar_logs",
    "NOME_ARQUIVO_LOG",
    "CAMINHO_PASTA_LOGS"
]
