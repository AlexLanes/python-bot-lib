# std
import sys, logging
from atexit import register as agendar_execucao
from datetime import (
    datetime as Datetime,
    timezone as Timezone,
    timedelta as Timedelta
)
# interno
import bot
from bot import configfile as cf

TIMEZONE = Timezone(Timedelta(hours=-3))
INICIALIZADO_EM = Datetime.now(TIMEZONE)

FORMATO_DATA_LOG = "%Y-%m-%dT%H:%M:%S"
FORMATO_NOME_LOG_PERSISTENCIA = "%Y-%m-%dT%H-%M-%S.log"
FORMATO_MENSAGEM_LOG = "%(asctime)s | nome(%(name)s) | level(%(levelname)s) | %(message)s"

CAMINHO_LOG_ATUAL = bot.windows.caminho_absoluto(".log")
CAMINHO_PASTA_LOGS_PERSISTENCIA  = bot.windows.caminho_absoluto("./logs")
CAMINHO_LOG_PERSISTENCIA = "\\".join((
    CAMINHO_PASTA_LOGS_PERSISTENCIA,
    INICIALIZADO_EM.strftime(FORMATO_NOME_LOG_PERSISTENCIA)
))

HANDLERS_LOG = [
    logging.StreamHandler(sys.stdout),
    logging.FileHandler(CAMINHO_LOG_ATUAL, "w", "utf-8")
]

# adicionar a persistência do log
if cf.obter_opcao_ou("logger", "flag_persistencia", True):
    if not bot.windows.caminho_existe(CAMINHO_PASTA_LOGS_PERSISTENCIA):
        bot.windows.criar_pasta(CAMINHO_PASTA_LOGS_PERSISTENCIA)
    handler = logging.FileHandler(CAMINHO_LOG_PERSISTENCIA, "w", "utf-8")
    HANDLERS_LOG.insert(0, handler)

def criar_mensagem_padrao (mensagem: str) -> str:
    """Extrair informações do stack para adicionar na mensagem de log"""
    stack, diretorio_execucao = bot.estruturas.InfoStack(3), bot.windows.diretorio_execucao().caminho
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

def limpar_log () -> None:
    """Limpar o `CAMINHO_LOG_ATUAL`
    - Não afeta o `CAMINHO_LOG_PERSISTENCIA`"""
    handler: logging.FileHandler = HANDLERS_LOG.pop(-1)
    root.removeHandler(handler)
    handler.close()

    handler = logging.FileHandler(CAMINHO_LOG_ATUAL, "w", "utf-8")
    handler.setFormatter(logging.Formatter(FORMATO_MENSAGEM_LOG, FORMATO_DATA_LOG))
    HANDLERS_LOG.append(handler)
    root.addHandler(handler)

@agendar_execucao
def limpar_logs_persistencia () -> None:
    """Limpar os logs na pasta de persistência que ultrapassaram a data limite
    - Função executada automaticamente ao fim da execução"""
    if not bot.windows.caminho_existe(CAMINHO_PASTA_LOGS_PERSISTENCIA):
        return
    # obter limite
    dias = cf.obter_opcao_ou("logger", "dias_persistencia", 14)
    limite = Timedelta(days=dias)
    # limpar
    for caminho_log in bot.windows.listar_diretorio(CAMINHO_PASTA_LOGS_PERSISTENCIA).arquivos:
        nome = bot.windows.nome_base(caminho_log)
        data = Datetime.strptime(nome, FORMATO_NOME_LOG_PERSISTENCIA).astimezone(TIMEZONE)
        if INICIALIZADO_EM - data < limite: break
        bot.windows.apagar_arquivo(caminho_log)

"""inicializar no primeiro `import` do pacote"""
root = logging.getLogger()
logger = logging.getLogger("BOT")
logger.setLevel(logging.DEBUG if cf.obter_opcao_ou("logger", "flag_debug", False) else logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    handlers=HANDLERS_LOG,
    datefmt=FORMATO_DATA_LOG,
    format=FORMATO_MENSAGEM_LOG
)

__all__ = [
    "erro",
    "debug", 
    "alertar",
    "informar",
    "limpar_log",
    "CAMINHO_LOG_ATUAL",
    "CAMINHO_LOG_PERSISTENCIA"
]
