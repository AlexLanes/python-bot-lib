# std
import os, sys, logging, atexit
from datetime import (
    datetime as Datetime,
    timezone as Timezone,
    timedelta as Timedelta
)
# interno
from .. import configfile, windows, estruturas

TIMEZONE = Timezone(Timedelta(hours=-3))
INICIALIZADO_EM = Datetime.now(TIMEZONE)

FORMATO_MENSAGEM_LOG = "%(asctime)s | nome(%(name)s) | level(%(levelname)s) | %(message)s"
FORMATO_DATA_LOG, FORMATO_NOME_LOG_PERSISTENCIA = "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H-%M-%S.log"
FORMATTER = logging.Formatter(FORMATO_MENSAGEM_LOG, FORMATO_DATA_LOG)

CAMINHO_PACOTE = windows.nome_diretorio(__file__).removesuffix(r"\logger")
DIRETORIO_EXECUCAO = CAMINHO_LOG_PERSISTENCIA = CAMINHO_PASTA_LOGS_PERSISTENCIA = CAMINHO_LOG_ATUAL = os.getcwd()

INICIALIZADO = False
ROOT_LOGGER, BOT_LOGGER = logging.getLogger(), logging.getLogger("BOT")

def inicializar () -> None:
    """Inicializar o logger
    - Utiliza o `configfile`"""
    assert windows.afirmar_diretorio(DIRETORIO_EXECUCAO)
    global CAMINHO_LOG_ATUAL, CAMINHO_PASTA_LOGS_PERSISTENCIA, CAMINHO_LOG_PERSISTENCIA
    CAMINHO_LOG_ATUAL = os.path.join(DIRETORIO_EXECUCAO, ".log")
    CAMINHO_PASTA_LOGS_PERSISTENCIA = os.path.join(DIRETORIO_EXECUCAO, "logs")
    CAMINHO_LOG_PERSISTENCIA = os.path.join(
        CAMINHO_PASTA_LOGS_PERSISTENCIA,
        INICIALIZADO_EM.strftime(FORMATO_NOME_LOG_PERSISTENCIA)
    )

    logging.basicConfig(
        force = True,
        encoding = "utf-8",
        datefmt = FORMATO_DATA_LOG,
        format = FORMATO_MENSAGEM_LOG,
        level = logging.DEBUG if configfile.obter_opcao_ou("logger", "flag_debug", False) else logging.INFO,
        handlers = [logging.FileHandler(CAMINHO_LOG_ATUAL, "w", "utf-8"), logging.StreamHandler(sys.stdout)]
    )

    # adicionar a persistência do log se requisitado
    if configfile.obter_opcao_ou("logger", "flag_persistencia", True):
        if not windows.caminho_existe(CAMINHO_PASTA_LOGS_PERSISTENCIA):
            windows.criar_pasta(CAMINHO_PASTA_LOGS_PERSISTENCIA)
        handler = logging.FileHandler(CAMINHO_LOG_PERSISTENCIA, "w", "utf-8")
        handler.setFormatter(FORMATTER)
        ROOT_LOGGER.addHandler(handler)

    global INICIALIZADO
    INICIALIZADO = True

def criar_mensagem_padrao (mensagem: str) -> str:
    """Extrair informações do stack para adicionar na mensagem de log"""
    if not INICIALIZADO: inicializar()
    stack = estruturas.InfoStack(3)
    prefixo_caminho = DIRETORIO_EXECUCAO if stack.caminho.startswith(DIRETORIO_EXECUCAO) else CAMINHO_PACOTE.removesuffix(r"\bot")
    arquivo_relativo = os.path.join(stack.caminho.removeprefix(prefixo_caminho), stack.nome)
    return f"arquivo({arquivo_relativo.lstrip("\\")}) | função({stack.funcao}) | linha({stack.linha}) | {mensagem}"

def debug (mensagem: str) -> None:
    """Log nível 'DEBUG'"""
    BOT_LOGGER.debug(criar_mensagem_padrao(mensagem))

def informar (mensagem: str) -> None:
    """Log nível 'INFO'"""
    BOT_LOGGER.info(criar_mensagem_padrao(mensagem))

def alertar (mensagem: str) -> None:
    """Log nível 'WARNING'"""
    BOT_LOGGER.warning(criar_mensagem_padrao(mensagem))

def erro (mensagem: str) -> None:
    """Log nível 'ERROR'
    - Erro é informado automaticamente no log"""
    BOT_LOGGER.error(criar_mensagem_padrao(mensagem), exc_info=sys.exc_info())

def limpar_log () -> None:
    """Limpar o `CAMINHO_LOG_ATUAL`
    - Não afeta o `CAMINHO_LOG_PERSISTENCIA`"""
    if not INICIALIZADO: return
    ROOT_LOGGER.handlers[0].close()
    handler = logging.FileHandler(CAMINHO_LOG_ATUAL, "w", "utf-8")
    handler.setFormatter(FORMATTER)
    ROOT_LOGGER.handlers[0] = handler

@atexit.register
def limpar_logs_persistencia () -> None:
    """Limpar os logs na pasta de persistência que ultrapassaram a data limite
    - Função executada automaticamente ao fim da execução"""
    if not INICIALIZADO or not windows.caminho_existe(CAMINHO_PASTA_LOGS_PERSISTENCIA):
        return
    # obter limite
    dias = configfile.obter_opcao_ou("logger", "dias_persistencia", 14)
    limite = Timedelta(days=dias)
    # limpar
    for caminho_log in windows.listar_diretorio(CAMINHO_PASTA_LOGS_PERSISTENCIA).arquivos:
        nome = windows.nome_base(caminho_log)
        data = Datetime.strptime(nome, FORMATO_NOME_LOG_PERSISTENCIA).astimezone(TIMEZONE)
        if INICIALIZADO_EM - data < limite: break
        windows.apagar_arquivo(caminho_log)

__all__ = [
    "erro",
    "debug", 
    "alertar",
    "informar",
    "limpar_log",
    "CAMINHO_LOG_ATUAL",
    "CAMINHO_LOG_PERSISTENCIA"
]
