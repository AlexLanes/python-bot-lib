# std
import sys, logging, atexit
from datetime import (
    datetime as Datetime,
    timezone as Timezone,
    timedelta as Timedelta
)
# interno
from .. import configfile, estruturas

TIMEZONE = Timezone(Timedelta(hours=-3))
INICIALIZADO_EM = Datetime.now(TIMEZONE)

FORMATO_MENSAGEM_LOG = "%(asctime)s | nome(%(name)s) | level(%(levelname)s) | %(message)s"
FORMATO_DATA_LOG, FORMATO_NOME_LOG_PERSISTENCIA = "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H-%M-%S.log"
FORMATTER = logging.Formatter(FORMATO_MENSAGEM_LOG, FORMATO_DATA_LOG)

CAMINHO_PACOTE = estruturas.Caminho(__file__).parente.string.removesuffix(r"\logger")
DIRETORIO_EXECUCAO = estruturas.Caminho.diretorio_execucao()
CAMINHO_LOG_ATUAL = DIRETORIO_EXECUCAO / ".log"
CAMINHO_DIRETORIO_PERSISTENCIA = DIRETORIO_EXECUCAO / "logs"
CAMINHO_LOG_PERSISTENCIA = CAMINHO_DIRETORIO_PERSISTENCIA / INICIALIZADO_EM.strftime(FORMATO_NOME_LOG_PERSISTENCIA)

INICIALIZADO = False
ROOT_LOGGER, BOT_LOGGER = logging.getLogger(), logging.getLogger("BOT")

def inicializar () -> None:
    """Inicializar o logger
    - Utiliza o `configfile`"""
    assert DIRETORIO_EXECUCAO.diretorio()
    global CAMINHO_LOG_ATUAL, CAMINHO_DIRETORIO_PERSISTENCIA, CAMINHO_LOG_PERSISTENCIA
    CAMINHO_LOG_ATUAL = DIRETORIO_EXECUCAO / ".log"
    CAMINHO_DIRETORIO_PERSISTENCIA = DIRETORIO_EXECUCAO / "logs"
    CAMINHO_LOG_PERSISTENCIA = CAMINHO_DIRETORIO_PERSISTENCIA / INICIALIZADO_EM.strftime(FORMATO_NOME_LOG_PERSISTENCIA)

    logging.basicConfig(
        force = True,
        encoding = "utf-8",
        datefmt = FORMATO_DATA_LOG,
        format = FORMATO_MENSAGEM_LOG,
        level = logging.DEBUG if configfile.obter_opcao_ou("logger", "flag_debug", False) else logging.INFO,
        handlers = [logging.FileHandler(CAMINHO_LOG_ATUAL.string, "w", "utf-8"), logging.StreamHandler(sys.stdout)]
    )

    # adicionar a persistência do log se requisitado
    if configfile.obter_opcao_ou("logger", "flag_persistencia", True):
        CAMINHO_DIRETORIO_PERSISTENCIA.criar_diretorios()
        handler = logging.FileHandler(CAMINHO_LOG_PERSISTENCIA.string, "w", "utf-8")
        handler.setFormatter(FORMATTER)
        ROOT_LOGGER.addHandler(handler)

    global INICIALIZADO
    INICIALIZADO = True

def caminho_log_atual () -> estruturas.Caminho:
    """Caminho para o arquivo log que é criado na raiz do projeto e que pode ser limpo pelo `limpar_log()`"""
    return CAMINHO_LOG_ATUAL

def caminho_log_persistencia () -> estruturas.Caminho:
    """Caminho para o arquivo log que é criado na inicialização do bot, se requisitado, para persistência na pasta `/logs`"""
    return CAMINHO_LOG_PERSISTENCIA

def criar_mensagem_padrao (mensagem: str) -> str:
    """Extrair informações do stack para adicionar na mensagem de log"""
    if not INICIALIZADO: inicializar()
    stack = estruturas.InfoStack(3)
    prefixo_caminho = DIRETORIO_EXECUCAO.string if str(stack.caminho).startswith(DIRETORIO_EXECUCAO.string) else CAMINHO_PACOTE.removesuffix(r"\bot")
    arquivo_relativo = str(stack.caminho).removeprefix(prefixo_caminho).lstrip("\\")
    return f"arquivo({arquivo_relativo}) | função({stack.funcao}) | linha({stack.linha}) | {mensagem}"

def debug (mensagem: str) -> None:
    """Log nível 'DEBUG'"""
    BOT_LOGGER.debug(criar_mensagem_padrao(mensagem))

def informar (mensagem: str) -> None:
    """Log nível 'INFO'"""
    BOT_LOGGER.info(criar_mensagem_padrao(mensagem))

def alertar (mensagem: str) -> None:
    """Log nível 'WARNING'"""
    BOT_LOGGER.warning(criar_mensagem_padrao(mensagem))

def erro (mensagem: str, excecao: Exception | None = None) -> None:
    """Log nível 'ERROR'
    - `excecao` Informação para o Traceback. Capturado automaticamente no `try except`"""
    BOT_LOGGER.error(
        criar_mensagem_padrao(mensagem),
        exc_info = excecao or sys.exc_info()
    )

def limpar_log () -> None:
    """Limpar o `CAMINHO_LOG_ATUAL`
    - Não afeta o `CAMINHO_LOG_PERSISTENCIA`"""
    if not INICIALIZADO: return
    ROOT_LOGGER.handlers[0].close()
    handler = logging.FileHandler(CAMINHO_LOG_ATUAL.string, "w", "utf-8")
    handler.setFormatter(FORMATTER)
    ROOT_LOGGER.handlers[0] = handler

@atexit.register
def limpar_logs_persistencia () -> None:
    """Limpar os logs no diretório de persistência que ultrapassaram a data limite
    - Função executada automaticamente ao fim da execução"""
    if not INICIALIZADO or not CAMINHO_DIRETORIO_PERSISTENCIA.existe():
        return
    # obter limite
    dias = configfile.obter_opcao_ou("logger", "dias_persistencia", 14)
    limite = Timedelta(days=dias)
    # limpar
    for caminho in CAMINHO_DIRETORIO_PERSISTENCIA:
        if not caminho.arquivo(): continue
        data = Datetime.strptime(caminho.nome, FORMATO_NOME_LOG_PERSISTENCIA).astimezone(TIMEZONE)
        if INICIALIZADO_EM - data < limite: break
        caminho.apagar_arquivo()

__all__ = [
    "erro",
    "debug", 
    "alertar",
    "informar",
    "limpar_log",
    "caminho_log_atual",
    "caminho_log_persistencia"
]
