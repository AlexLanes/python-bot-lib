# std
import sys
import logging
from atexit import register as executar_no_fim
from datetime import datetime, timedelta, timezone
# interno
import bot
from bot import configfile as cf


NOME_ARQUIVO_LOG = ".log" # útima execução
CAMINHO_PASTA_LOGS  = "./logs"
FORMATO_NOME_LOG = "%Y-%m-%dT%H-%M-%S.log"
DATA_INICIALIZACAO = datetime.now(timezone(timedelta(hours=-3)))
HANDLERS_LOG = [logging.StreamHandler(sys.stdout), logging.FileHandler(NOME_ARQUIVO_LOG, "w", "utf-8")]


# adicionar a persistência do log. Default: True
if cf.obter_opcao("logger", "flag_persistencia", "True").lower() == "true":
    nome = f"{CAMINHO_PASTA_LOGS}/{DATA_INICIALIZACAO.strftime(FORMATO_NOME_LOG)}"
    if not bot.windows.caminho_existe(CAMINHO_PASTA_LOGS): bot.windows.criar_pasta(CAMINHO_PASTA_LOGS)
    HANDLERS_LOG.append(logging.FileHandler(nome, "w", "utf-8"))


logger = logging.getLogger("BOT")
logger.setLevel(logging.DEBUG if cf.obter_opcao("logger", "flag_debug", "True").lower() == "true" else logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S",
    format="%(asctime)s | nome(%(name)s) | level(%(levelname)s) | %(message)s",
    handlers = HANDLERS_LOG
)


def criar_mensagem_padrao (mensagem: str) -> str:
    """Extrair informações do stack para adicionar na mensagem de log"""
    stack, diretorio_execucao = bot.util.obter_info_stack(3), bot.windows.diretorio_execucao().caminho
    caminho = rf"{stack.caminho.removeprefix(diretorio_execucao)}\{stack.nome}".lstrip("\\")
    return f"arquivo({caminho}) | função({stack.funcao}) | linha({stack.linha}) | {mensagem}"


def debug (mensagem: str) -> None:
    """Log nível 'DEBUG'"""
    logger.debug(criar_mensagem_padrao(mensagem))


def informar (mensagem: str) -> None:
    """Log nível 'INFO'"""
    logger.info(criar_mensagem_padrao(mensagem))


def alertar (mensagem: str) -> None:
    """Log nível 'WARNING'"""
    logger.warning(criar_mensagem_padrao(mensagem))


def erro (mensagem: str) -> None:
    """Log nível 'ERROR'
    - Erro é informado automaticamente no log"""
    logger.error(criar_mensagem_padrao(mensagem), exc_info=sys.exc_info())


@executar_no_fim
def limpar_logs () -> None:
    """Limpar os logs que ultrapassaram a data limite
    - Função executada automaticamente ao fim da execução"""
    # obter limite
    dias = int(cf.obter_opcao("logger", "dias_persistencia", "14"))
    limite = timedelta(days=dias)

    # checar caminho
    caminho = bot.windows.caminho_absoluto(CAMINHO_PASTA_LOGS)
    if not bot.windows.caminho_existe(caminho): return

    # limpar
    for caminho_log in bot.windows.listar_diretorio(caminho).arquivos:
        nome = bot.windows.extrair_nome_base(caminho_log)
        data = datetime.strptime(nome, FORMATO_NOME_LOG)
        if datetime.now() - data > limite: bot.windows.apagar_arquivo(caminho_log)


__all__ = [
    "erro",
    "debug", 
    "alertar",
    "informar",
    "NOME_ARQUIVO_LOG"
]
